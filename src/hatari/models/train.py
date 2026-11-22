"""Fit the selected model on the whole training part and save it.

The selected configuration is fixed in ``SELECTED``, as recorded in
docs/05_model_comparison.md. A linear SVM returns a margin, not a probability,
so its margin is calibrated by Platt scaling. The calibration uses the
out-of-fold margins of the same grouped folds as the model selection, and the
final SVM is then fitted on the whole training part (``ensemble=False``).

Usage, from the repository root, after python -m hatari.data.corpus:

    python -m hatari.models.train
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV

from hatari.data.corpus import PROCESSED_DIR

from .candidates import Candidate, build
from .selection import fold_assignment, load_training

MODELS_DIR = Path(__file__).resolve().parents[3] / "models"
MODEL_FILE = "hatari_model.joblib"
METADATA_FILE = "hatari_model.json"
SELECTED = Candidate("SVM", "mask", 1.0)
THRESHOLD = 0.5


def grouped_splits(frame):
    folds = fold_assignment(frame)
    return [(np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)) for fold in np.unique(folds)]


def fit(frame, candidate: Candidate = SELECTED) -> CalibratedClassifierCV:
    model = CalibratedClassifierCV(build(candidate), method="sigmoid", cv=grouped_splits(frame), ensemble=False)
    return model.fit(frame["text"], frame["suspicious"].astype(bool))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    training = load_training()
    model = fit(training)
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODELS_DIR / MODEL_FILE)
    metadata = {
        "configuration": SELECTED.name,
        "calibration": "Platt scaling on out-of-fold margins of five grouped folds",
        "threshold": THRESHOLD,
        "training_messages": int(len(training)),
        "training_by_language": training["language"].value_counts().to_dict(),
        "corpus_sha256": file_sha256(PROCESSED_DIR / "corpus.csv"),
        "model_sha256": file_sha256(MODELS_DIR / MODEL_FILE),
        "scikit_learn": sklearn.__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (MODELS_DIR / METADATA_FILE).write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
