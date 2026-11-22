"""Grouped cross-validation of the candidates and selection rule of docs/04_modelling_protocol.md.

Usage, from the repository root, after python -m hatari.data.corpus:

    python -m hatari.models.selection

Writes reports/cross_validation.csv, one row per candidate and language.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold

from hatari.data.corpus import PROCESSED_DIR, TRAIN

from .candidates import SEED, Candidate, all_candidates, build, decision_scores, default_threshold

REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports"
FOLDS = 5
EQUIVALENCE = 0.01


def load_training(processed_dir=PROCESSED_DIR) -> pd.DataFrame:
    corpus = pd.read_csv(processed_dir / "corpus.csv")
    return corpus[corpus["split"] == TRAIN].reset_index(drop=True)


def fold_assignment(frame: pd.DataFrame, folds: int = FOLDS, seed: int = SEED) -> np.ndarray:
    """Fold of each row, with templates kept whole and both labels stratified."""
    groups = frame["language"] + ":" + frame["group"].astype(str)
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    assignment = np.full(len(frame), -1)
    for fold, (_, index) in enumerate(splitter.split(frame, frame["suspicious"].astype(bool), groups)):
        assignment[index] = fold
    return assignment


def out_of_fold_scores(candidate: Candidate, frame: pd.DataFrame, folds: np.ndarray) -> np.ndarray:
    scores = np.empty(len(frame))
    template = build(candidate)
    for fold in np.unique(folds):
        train, held = folds != fold, folds == fold
        model = clone(template).fit(frame.loc[train, "text"], frame.loc[train, "suspicious"])
        scores[held] = decision_scores(model, frame.loc[held, "text"])
    return scores


def metrics(truth, scores, threshold: float) -> dict:
    truth = np.asarray(truth, dtype=bool)
    predicted = np.asarray(scores) > threshold
    tn, fp, fn, tp = confusion_matrix(truth, predicted, labels=[False, True]).ravel()
    return {
        "messages": len(truth), "precision": precision_score(truth, predicted, zero_division=0),
        "recall": recall_score(truth, predicted, zero_division=0), "f1": f1_score(truth, predicted, zero_division=0),
        "accuracy": accuracy_score(truth, predicted), "average_precision": average_precision_score(truth, scores),
        "true_negatives": tn, "false_positives": fp, "false_negatives": fn, "true_positives": tp,
    }


def evaluate(candidates: list[Candidate], frame: pd.DataFrame) -> pd.DataFrame:
    folds = fold_assignment(frame)
    rows = []
    for candidate in candidates:
        scores = out_of_fold_scores(candidate, frame, folds)
        for language, part in frame.groupby("language"):
            row = metrics(part["suspicious"], scores[part.index], default_threshold(candidate))
            rows.append({"candidate": candidate.name, "family": candidate.family,
                         "preprocessing": candidate.preprocessing, "c": candidate.c, "language": language, **row})
        print(f"{candidate.name} done", flush=True)
    return pd.DataFrame(rows)


def select(results: pd.DataFrame, candidates: list[Candidate], equivalence: float = EQUIVALENCE) -> Candidate:
    """Apply the selection rule to the English out-of-fold scores."""
    english = results[results["language"] == "en"].set_index("candidate")
    best_f1 = english["f1"].max()
    tied = english[english["f1"] >= best_f1 - equivalence]
    best_recall = tied["recall"].max()
    tied = tied[tied["recall"] >= best_recall - equivalence]
    by_name = {candidate.name: candidate for candidate in candidates}
    return min((by_name[name] for name in tied.index), key=lambda candidate: candidate.simplicity_rank)


def main() -> None:
    training = load_training()
    candidates = all_candidates()
    results = evaluate(candidates, training)
    REPORTS_DIR.mkdir(exist_ok=True)
    results.round(4).to_csv(REPORTS_DIR / "cross_validation.csv", index=False)
    chosen = select(results, candidates)
    view = results.pivot_table(index="candidate", columns="language", values=["f1", "recall", "precision"])
    print(view.round(3).sort_values(("f1", "en"), ascending=False).to_string())
    print("selected", chosen.name)


if __name__ == "__main__":
    main()
