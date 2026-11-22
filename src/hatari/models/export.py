"""Copy the trained model into app/ressources for deployment.

The model of models/ is not versioned, since it is rebuilt by the pipeline. A
hosted interface cannot run the pipeline, so the deployed copy is versioned in
app/ressources, with its description. The copy is checked against the checksum
recorded at training.

Usage, from the repository root, after python -m hatari.models.train:

    python -m hatari.models.export
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .train import METADATA_FILE, MODEL_FILE, MODELS_DIR, file_sha256

RESOURCES_DIR = Path(__file__).resolve().parents[3] / "app" / "ressources"


def verify(directory: Path) -> str:
    """Return the checksum of the model of a directory, after checking it against its description."""
    metadata = json.loads((directory / METADATA_FILE).read_text())
    checksum = file_sha256(directory / MODEL_FILE)
    if checksum != metadata["model_sha256"]:
        raise ValueError(f"{directory / MODEL_FILE} does not match the checksum of its description")
    return checksum


def export(source: Path = MODELS_DIR, target: Path = RESOURCES_DIR) -> str:
    verify(source)
    target.mkdir(parents=True, exist_ok=True)
    for name in [MODEL_FILE, METADATA_FILE]:
        shutil.copy2(source / name, target / name)
    return verify(target)


if __name__ == "__main__":
    print("exported model", export())
