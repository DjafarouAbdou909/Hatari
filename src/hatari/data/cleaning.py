"""Removal of generator artefacts from the French synthetic dataset.

The generator of the French synthetic dataset appends a marker that reveals the
label. Every legitimate message ends with a reference such as
``[référence SM-00001]`` or ``[référence EM-01837]``, and every spam message
contains a fragment such as ``Dossier Lyon-1000.``. A model would learn these
markers instead of the content, so they are removed before any use. Real
messages are never altered by this module.
"""

from __future__ import annotations

import re

LEGITIMATE_MARKER = re.compile(r"\s*\[référence (?:SM|EM)-\d+\]")
SPAM_MARKER = re.compile(r"\s*Dossier [A-ZÉ][\wéèêëàâîïôûç'-]*-\d+\.?")


def strip_generator_markers(text: str) -> str:
    text = LEGITIMATE_MARKER.sub("", text)
    text = SPAM_MARKER.sub("", text)
    return text.strip()


def has_generator_marker(text: str) -> bool:
    return bool(LEGITIMATE_MARKER.search(text) or SPAM_MARKER.search(text))
