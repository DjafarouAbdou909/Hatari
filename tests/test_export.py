import json

import pytest

from hatari.models.export import RESOURCES_DIR, export, verify
from hatari.models.train import METADATA_FILE, MODEL_FILE, file_sha256


def _model(directory, content=b"model"):
    directory.mkdir()
    (directory / MODEL_FILE).write_bytes(content)
    (directory / METADATA_FILE).write_text(json.dumps({"model_sha256": file_sha256(directory / MODEL_FILE)}))
    return directory


def test_export_copies_and_verifies(tmp_path):
    source = _model(tmp_path / "models")
    assert export(source, tmp_path / "ressources") == file_sha256(source / MODEL_FILE)


def test_a_modified_model_is_rejected(tmp_path):
    source = _model(tmp_path / "models")
    (source / MODEL_FILE).write_bytes(b"tampered")
    with pytest.raises(ValueError):
        verify(source)


@pytest.mark.skipif(not (RESOURCES_DIR / MODEL_FILE).exists(), reason="no deployed model")
def test_the_deployed_model_matches_its_description():
    verify(RESOURCES_DIR)
