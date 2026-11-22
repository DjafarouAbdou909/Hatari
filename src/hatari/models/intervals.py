"""Confidence intervals of the reported scores, added on 22 November 2026.

Cross-validation. Out-of-fold predictions are recomputed, on the same folds as
the selection, for the selected configuration, the best configuration by F1,
the best word logistic regression and the best Naive Bayes. Each gets a grouped
bootstrap interval on English real messages, and the F1 difference with the
selected configuration gets a paired interval. These intervals do not change
the selection, which was fixed by the protocol.

Test. The saved model is applied again to the test set, which reproduces the
predictions of reports/test_errors.csv. Only intervals are added, no choice is
made from them.

Usage, from the repository root, after python -m hatari.models.train:

    python -m hatari.models.intervals

Writes reports/cv_intervals.csv and reports/test_intervals.csv.
"""

from __future__ import annotations

import joblib
import pandas as pd

from .candidates import Candidate, default_threshold
from .evaluate import load_test
from .selection import REPORTS_DIR, fold_assignment, load_training, out_of_fold_scores
from .train import MODEL_FILE, MODELS_DIR, SELECTED, THRESHOLD
from .uncertainty import grouped_bootstrap, paired_difference

COMPARED = [SELECTED, Candidate("SVM-char", "normalize", 0.1), Candidate("LR", "mask", 10.0), Candidate("NB", "mask")]


def group_key(frame: pd.DataFrame) -> pd.Series:
    return frame["language"] + ":" + frame["group"].astype(str)


def interval_rows(name: str, part: pd.DataFrame, predicted, reference=None) -> dict:
    intervals = grouped_bootstrap(part["suspicious"], predicted, group_key(part))
    row = {"candidate": name, "messages": len(part), "groups": group_key(part).nunique()}
    for metric, (low, high) in intervals.items():
        row[f"{metric}_low"], row[f"{metric}_high"] = low, high
    if reference is not None:
        difference = paired_difference(part["suspicious"], predicted, reference, group_key(part))
        row.update({"f1_minus_selected": difference["difference"], "difference_low": difference["low"],
                    "difference_high": difference["high"]})
    return row


def cross_validation_intervals() -> pd.DataFrame:
    training = load_training()
    folds = fold_assignment(training)
    english = training[training["language"] == "en"]
    predictions = {}
    for candidate in COMPARED:
        scores = out_of_fold_scores(candidate, training, folds)
        predictions[candidate.name] = scores[english.index] > default_threshold(candidate)
        print(f"{candidate.name} done", flush=True)
    selected = predictions[SELECTED.name]
    rows = [interval_rows(name, english, predicted, None if name == SELECTED.name else selected)
            for name, predicted in predictions.items()]
    return pd.DataFrame(rows)


def test_intervals() -> pd.DataFrame:
    model = joblib.load(MODELS_DIR / MODEL_FILE)
    test = load_test()
    predicted = model.predict_proba(test["text"])[:, 1] > THRESHOLD
    rows = []
    for language, part in test.groupby("language"):
        rows.append({"language": language, **interval_rows(SELECTED.name, part, predicted[part.index])})
    return pd.DataFrame(rows)


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    test = test_intervals()
    test.round(4).to_csv(REPORTS_DIR / "test_intervals.csv", index=False)
    print(test.round(3).to_string(index=False))
    cross = cross_validation_intervals()
    cross.round(4).to_csv(REPORTS_DIR / "cv_intervals.csv", index=False)
    print(cross.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
