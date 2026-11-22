"""Build the modelling corpus and its leakage-free partition.

English real data. UCI and Mendeley are merged and deduplicated by exact key,
because 4,943 texts appear in both. When a text is in both, the UCI text is
kept, since Mendeley damaged some characters. The two sources agree on the
binary label of every shared text.

Partition. Messages that differ only by their digits share a template key and
always fall in the same part. One fifth of the English templates is held out as
the test set, stratified on the target. The French synthetic data keeps its
published split, which already separates its template families, and its
validation part joins its training part.

Usage, from the repository root:

    python -m hatari.data.corpus
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .audit import exact_key, template_key
from .sources import load_all

PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
SEED = 20261122
TEST_FOLDS = 5
TRAIN, TEST = "train", "test"


def english_corpus(uci: pd.DataFrame, mendeley: pd.DataFrame) -> pd.DataFrame:
    """Merge the two English sources into one row per distinct text."""
    frame = pd.concat([uci, mendeley], ignore_index=True)
    frame["key"] = frame["text"].map(exact_key)
    conflicts = frame.groupby("key")["suspicious"].nunique().gt(1)
    if conflicts.any():
        raise ValueError(f"{int(conflicts.sum())} texts carry both binary labels")
    sources = frame.groupby("key")["source"].agg(lambda s: "+".join(sorted(set(s))))
    merged = frame.drop_duplicates("key", keep="first").copy()
    merged["sources"] = merged["key"].map(sources)
    merged["group"] = merged["text"].map(template_key)
    return merged.reset_index(drop=True)


def assign_english_split(frame: pd.DataFrame, seed: int = SEED) -> pd.Series:
    """Hold out one of five stratified folds of templates as the test set."""
    folds = StratifiedGroupKFold(n_splits=TEST_FOLDS, shuffle=True, random_state=seed)
    _, test_index = next(folds.split(frame, frame["suspicious"], frame["group"]))
    split = pd.Series(TRAIN, index=frame.index)
    split.iloc[test_index] = TEST
    return split


def french_corpus(synthetic: pd.DataFrame) -> pd.DataFrame:
    frame = synthetic.copy()
    frame["key"] = frame["text"].map(exact_key)
    frame["sources"] = frame["source"]
    frame["group"] = frame["template_group"]
    frame["split"] = frame["published_split"].replace({"validation": TRAIN})
    return frame


def build_corpus(sources: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    sources = sources or load_all()
    english = english_corpus(sources["uci_sms_spam"], sources["mendeley_smishing"])
    english["split"] = assign_english_split(english)
    french = french_corpus(sources["french_synthetic"])
    columns = ["language", "origin", "channel", "sources", "source", "row", "text", "original_label",
               "suspicious", "group", "split"]
    corpus = pd.concat([english[columns], french[columns]], ignore_index=True)
    corpus.insert(0, "message_id", [f"m{i:05d}" for i in range(len(corpus))])
    return corpus


def main() -> None:
    corpus = build_corpus()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    corpus.to_csv(PROCESSED_DIR / "corpus.csv", index=False)
    table = corpus.groupby(["language", "origin", "split"])["suspicious"].agg(["size", "sum", "mean"])
    print(table.round(4).to_string())


if __name__ == "__main__":
    main()
