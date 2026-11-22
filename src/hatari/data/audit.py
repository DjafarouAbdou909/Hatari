"""Reproducible statistics for the data audit of docs/02_data_audit.md.

Usage, from the repository root:

    python -m hatari.data.audit
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from .download import RAW_DIR
from .sources import load_all

REPLACEMENT_CHARACTER = "\ufffd"


def exact_key(text: str) -> str:
    """Key under which two messages are the same text up to case, spacing and punctuation."""
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[\W_]+", "", text)


def template_key(text: str) -> str:
    """Key under which two messages differ only by their digits, such as numbers or amounts."""
    return re.sub(r"\d+", "0", exact_key(text))


def summary(frame: pd.DataFrame) -> dict:
    keys = frame["text"].map(exact_key)
    templates = frame["text"].map(template_key)
    conflicting = frame.groupby(keys)["suspicious"].nunique().gt(1).sum()
    return {
        "messages": len(frame),
        "suspicious": int(frame["suspicious"].sum()),
        "suspicious_share": round(float(frame["suspicious"].mean()), 4),
        "labels": frame["original_label"].value_counts().to_dict(),
        "channels": frame["channel"].value_counts().to_dict(),
        "duplicate_messages": int(keys.duplicated().sum()),
        "distinct_texts": int(keys.nunique()),
        "distinct_templates": int(templates.nunique()),
        "binary_label_conflicts": int(conflicting),
        "replacement_characters": int(frame["text"].str.contains(REPLACEMENT_CHARACTER).sum()),
        "median_characters": int(frame["text"].str.len().median()),
    }


def overlap(first: pd.DataFrame, second: pd.DataFrame) -> dict:
    """Distinct texts shared by two sources and the agreement of their labels."""
    a = first.assign(key=first["text"].map(exact_key)).drop_duplicates("key")
    b = second.assign(key=second["text"].map(exact_key)).drop_duplicates("key")
    shared = a.merge(b, on="key", suffixes=("_first", "_second"))
    return {
        "shared_texts": len(shared),
        "only_first": int((~a["key"].isin(b["key"])).sum()),
        "only_second": int((~b["key"].isin(a["key"])).sum()),
        "label_crosstab": pd.crosstab(shared["original_label_first"], shared["original_label_second"]).to_dict(),
    }


def split_leakage(frame: pd.DataFrame, split: str = "published_split") -> dict:
    """Texts and digit templates found in more than one split of a published partition."""
    keys = frame["text"].map(exact_key)
    templates = frame["text"].map(template_key)
    return {
        "texts_in_several_splits": int(frame.groupby(keys)[split].nunique().gt(1).sum()),
        "templates_in_several_splits": int(frame.groupby(templates)[split].nunique().gt(1).sum()),
    }


def translated_french_defects(raw_dir=RAW_DIR) -> dict:
    """Lines of the machine-translated French file that do not follow its label,text,,, layout."""
    lines = (raw_dir / "french_translated.csv").read_text(encoding="utf-8").split("\n")
    filled = [line for line in lines if line]
    labelled = [line for line in filled if line.split(",", 1)[0] in {"ham", "spam"}]
    return {
        "non_empty_lines": len(filled),
        "lines_with_a_label": len(labelled),
        "labels": pd.Series([line.split(",", 1)[0] for line in labelled]).value_counts().to_dict(),
        "lines_without_a_label": len(filled) - len(labelled),
        "examples_without_a_label": [line[:90] for line in filled if line not in labelled][:4],
    }


def main() -> None:
    sources = load_all()
    for name, frame in sources.items():
        print(name, summary(frame))
    print("uci and mendeley", overlap(sources["uci_sms_spam"], sources["mendeley_smishing"]))
    synthetic = sources["french_synthetic"]
    print("french_synthetic splits", synthetic["published_split"].value_counts().to_dict())
    print("french_synthetic categories", synthetic["spam_category"].value_counts().to_dict())
    print("french_synthetic leakage", split_leakage(synthetic))
    print("french_translated defects", translated_french_defects())


if __name__ == "__main__":
    main()
