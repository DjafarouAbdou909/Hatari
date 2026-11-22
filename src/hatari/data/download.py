"""Download the public datasets used by HATARI into data/raw.

Each source is pinned to a URL and, once verified, to a SHA-256 checksum, so
that a later download that differs from the audited file is detected.

Usage, from the repository root:

    python -m hatari.data.download
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    filename: str
    sha256: str | None
    extract: bool = False


SOURCES = [
    Source(
        name="uci_sms_spam",
        url="https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
        filename="uci_sms_spam.zip",
        sha256="1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3",
        extract=True,
    ),
    Source(
        name="mendeley_smishing",
        url="https://data.mendeley.com/public-files/datasets/f45bkkt8pr/files/"
            "edb361de-918d-469f-9106-e84823830665/file_downloaded",
        filename="mendeley_smishing.zip",
        sha256="9bbf3188fdad81495d8e82825648b9b63b53fc86841a3d26c02629990b233cc3",
        extract=True,
    ),
    Source(
        name="french_translated",
        url="https://raw.githubusercontent.com/Djochrist/Kaggle-SMS-Spam-Collection-Dataset-French/"
            "master/spam_fr.csv",
        filename="french_translated.csv",
        sha256="ebfccd04514e184440a8de53b8ca57fc9bc300c7ae0f44417923d7e019ef093a",
    ),
    Source(
        name="french_synthetic",
        url="https://raw.githubusercontent.com/Djochrist/french-spam-text-dataset-v1.0/main/data/messages.csv",
        filename="french_synthetic.csv",
        sha256="8d8f9130838a0bea10bc4f99dbe563b2ca903f90be38aa13a9a57c46e33aac4d",
    ),
]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def download(source: Source, raw_dir: Path = RAW_DIR) -> Path:
    """Download one source if absent, check its checksum and extract archives."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / source.filename
    if not target.exists():
        request = urllib.request.Request(source.url, headers={"User-Agent": "hatari-dataset-downloader"})
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
    checksum = sha256_of(target)
    if source.sha256 is not None and checksum != source.sha256:
        raise ValueError(f"{source.name}: checksum {checksum} differs from the expected {source.sha256}")
    if source.extract:
        with zipfile.ZipFile(target) as archive:
            archive.extractall(raw_dir / source.name)
    print(f"{source.name}: {target.stat().st_size} bytes, sha256 {checksum}")
    return target


def main() -> int:
    for source in SOURCES:
        download(source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
