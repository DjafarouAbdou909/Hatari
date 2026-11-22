"""Exploratory analysis of the training part of the corpus, for docs/03_exploratory_analysis.md.

Only the training part is read, so that no observation of the test set can
influence the modelling choices.

Usage, from the repository root, after python -m hatari.data.corpus:

    python -m hatari.analysis.eda
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd

from hatari.data.corpus import PROCESSED_DIR, TRAIN

# Simple exploratory indicators. They are not the signals of the product.
INDICATORS = {
    "link": r"https?://|www\.|\b[\w-]+\.(?:com|net|org|co\.uk|ci|fr|ly|info|biz)\b",
    "phone_number": r"\+?\d[\d\s.-]{7,}\d",
    "money": r"£|\$|€|\bfcfa\b|\bcfa\b|\bcash\b|\bprize\b|\bgagn",
    "any_digit": r"\d",
    "free_or_win": r"\b(?:free|win|won|winner|gratuit|gagnez|gagné)\b",
    "urgency": r"\b(?:urgent|now|immediately|immédiatement|maintenant|today|aujourd'hui|expire)\b",
    "code_or_password": r"\b(?:pin|password|mot de passe|code|otp)\b",
}


def load_training(processed_dir=PROCESSED_DIR) -> pd.DataFrame:
    corpus = pd.read_csv(processed_dir / "corpus.csv")
    return corpus[corpus["split"] == TRAIN].reset_index(drop=True)


def indicator_rates(frame: pd.DataFrame) -> pd.DataFrame:
    flags = pd.DataFrame({name: frame["text"].str.contains(pattern, case=False, regex=True)
                          for name, pattern in INDICATORS.items()})
    return flags.groupby([frame["language"], frame["suspicious"]]).mean().round(3)


def shape(frame: pd.DataFrame) -> pd.DataFrame:
    letters = frame["text"].map(lambda s: sum(c.isalpha() for c in s))
    upper = frame["text"].map(lambda s: sum(c.isupper() for c in s))
    stats = frame.assign(characters=frame["text"].str.len(), words=frame["text"].str.split().str.len(),
                         uppercase_share=upper / letters.clip(lower=1))
    return stats.groupby(["language", "suspicious"])[["characters", "words", "uppercase_share"]].median().round(3)


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zà-ÿ']+", text.lower()))


def distinctive_words(frame: pd.DataFrame, minimum: int = 15, top: int = 15) -> dict[str, list[str]]:
    """Words with the highest and lowest smoothed log ratio of document frequency between classes."""
    suspicious, legitimate = Counter(), Counter()
    for text, label in zip(frame["text"], frame["suspicious"]):
        (suspicious if label else legitimate).update(tokens(text))
    n_suspicious, n_legitimate = int(frame["suspicious"].sum()), int((~frame["suspicious"]).sum())
    ratio = {word: np.log((suspicious[word] + 1) / (n_suspicious + 2)) - np.log((legitimate[word] + 1) / (n_legitimate + 2))
             for word in set(suspicious) | set(legitimate) if suspicious[word] + legitimate[word] >= minimum}
    ordered = pd.Series(ratio).sort_values()
    return {"suspicious": ordered.tail(top).index[::-1].tolist(), "legitimate": ordered.head(top).index.tolist()}


def main() -> None:
    training = load_training()
    print(training.groupby(["language", "suspicious"]).size().to_string(), "\n")
    print(shape(training).to_string(), "\n")
    print(indicator_rates(training).to_string(), "\n")
    for language, part in training.groupby("language"):
        print(language, distinctive_words(part, minimum=15 if language == "en" else 5))


if __name__ == "__main__":
    main()
