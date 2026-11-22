"""Load each raw dataset into one common schema.

Every loader returns a DataFrame with the columns of ``COLUMNS``:

- ``source``: dataset name, as in ``hatari.data.download.SOURCES``;
- ``row``: line of the message in its raw file, for traceability;
- ``language``: ``en`` or ``fr``;
- ``origin``: ``real`` for collected messages, ``synthetic`` for generated ones;
- ``channel``: ``sms`` or ``email``;
- ``text``: the message, unchanged except for surrounding whitespace;
- ``original_label``: the label as published, lower-cased;
- ``suspicious``: binary target, True for any message the source labels as spam, smishing or fraud.

The binary target is the only label shared by all sources. Finer labels are
kept in ``original_label`` for analysis but are not reliable enough to train on,
as documented in docs/02_data_audit.md.
"""

from __future__ import annotations

import csv

import pandas as pd

from .download import RAW_DIR

COLUMNS = ["source", "row", "language", "origin", "channel", "text", "original_label", "suspicious"]
LEGITIMATE_LABELS = {"ham", "legitimate"}


def _finish(frame: pd.DataFrame, source: str, language: str, origin: str) -> pd.DataFrame:
    frame = frame.assign(source=source, language=language, origin=origin)
    frame["text"] = frame["text"].astype(str).str.strip()
    frame["original_label"] = frame["original_label"].str.strip().str.lower()
    frame["suspicious"] = ~frame["original_label"].isin(LEGITIMATE_LABELS)
    return frame[COLUMNS].reset_index(drop=True)


def load_uci(raw_dir=RAW_DIR) -> pd.DataFrame:
    """UCI SMS Spam Collection, Almeida and Hidalgo 2011, labels ham and spam."""
    frame = pd.read_csv(raw_dir / "uci_sms_spam" / "SMSSpamCollection", sep="\t", header=None,
                        names=["original_label", "text"], quoting=csv.QUOTE_NONE, dtype=str,
                        keep_default_na=False)
    frame["row"] = frame.index + 1
    frame["channel"] = "sms"
    return _finish(frame, "uci_sms_spam", "en", "real")


def load_mendeley(raw_dir=RAW_DIR) -> pd.DataFrame:
    """SMS Phishing Dataset, Mishra and Soni 2022, labels ham, spam and smishing."""
    frame = pd.read_csv(raw_dir / "mendeley_smishing" / "Dataset_5971.csv", dtype=str, keep_default_na=False)
    frame = frame.rename(columns={"LABEL": "original_label", "TEXT": "text"})
    frame["row"] = frame.index + 2
    frame["channel"] = "sms"
    return _finish(frame, "mendeley_smishing", "en", "real")


def load_french_synthetic(raw_dir=RAW_DIR) -> pd.DataFrame:
    """Synthetic French SMS and emails, Djochrist version 1.1.0, labels spam and legitimate.

    The published split and template family are kept in ``published_split`` and
    ``template_group``, because messages of one family must stay in one split.
    """
    raw = pd.read_csv(raw_dir / "french_synthetic.csv", dtype=str, keep_default_na=False)
    frame = raw.rename(columns={"label": "original_label", "domain": "channel"})
    frame["row"] = frame.index + 2
    result = _finish(frame, "french_synthetic", "fr", "synthetic")
    result["published_split"] = raw["split"].to_numpy()
    result["template_group"] = raw["template_group"].to_numpy()
    result["spam_category"] = raw["spam_category"].to_numpy()
    return result


def load_all(raw_dir=RAW_DIR) -> dict[str, pd.DataFrame]:
    return {
        "uci_sms_spam": load_uci(raw_dir),
        "mendeley_smishing": load_mendeley(raw_dir),
        "french_synthetic": load_french_synthetic(raw_dir),
    }
