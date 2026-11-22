"""Single evaluation of the saved model on the test part of the corpus.

Writes reports/test_evaluation.csv, the metrics by language, and
reports/test_errors.csv, every misclassified test message with its score, for
the error analysis.

Usage, from the repository root, after python -m hatari.models.train:

    python -m hatari.models.evaluate
"""

from __future__ import annotations

import joblib
import pandas as pd

from hatari.data.corpus import PROCESSED_DIR, TEST

from .selection import REPORTS_DIR, metrics
from .train import MODEL_FILE, MODELS_DIR, THRESHOLD


def load_test(processed_dir=PROCESSED_DIR) -> pd.DataFrame:
    corpus = pd.read_csv(processed_dir / "corpus.csv")
    return corpus[corpus["split"] == TEST].reset_index(drop=True)


def evaluate(model, test: pd.DataFrame, threshold: float = THRESHOLD) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored = test.assign(score=model.predict_proba(test["text"])[:, 1])
    rows = [{"language": language, **metrics(part["suspicious"], part["score"], threshold)}
            for language, part in scored.groupby("language")]
    predicted = scored["score"] > threshold
    errors = scored[predicted != scored["suspicious"].astype(bool)].assign(
        error=lambda f: f["suspicious"].map({True: "false_negative", False: "false_positive"}))
    columns = ["message_id", "language", "sources", "original_label", "error", "score", "text"]
    return pd.DataFrame(rows), errors[columns].sort_values(["language", "error", "score"])


def main() -> None:
    model = joblib.load(MODELS_DIR / MODEL_FILE)
    results, errors = evaluate(model, load_test())
    REPORTS_DIR.mkdir(exist_ok=True)
    results.round(4).to_csv(REPORTS_DIR / "test_evaluation.csv", index=False)
    errors.round(4).to_csv(REPORTS_DIR / "test_errors.csv", index=False)
    print(results.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
