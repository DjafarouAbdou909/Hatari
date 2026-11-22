"""Normalisation defence against obfuscation, defined in docs/research_obfuscation.md.

It removes invisible format characters, maps Cyrillic and Greek letters that look
like Latin letters back to Latin, and joins single letters separated by dots,
hyphens or spaces when at least four follow each other. Digit substitution, as
in "c0de", is not reversed, because a digit is often meant as a digit.
"""

from __future__ import annotations

import re
import unicodedata

LOOK_ALIKES = {
    # Cyrillic
    "а": "a", "с": "c", "е": "e", "і": "i", "о": "o", "р": "p", "х": "x", "у": "y", "ѕ": "s", "ј": "j", "һ": "h",
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "І": "I", "Ј": "J", "К": "K", "М": "M", "О": "O", "Р": "P",
    "Ѕ": "S", "Т": "T", "Х": "X", "У": "Y",
    # Greek
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P",
    "Τ": "T", "Υ": "Y", "Χ": "X", "ο": "o",
}
TRANSLATION = str.maketrans(LOOK_ALIKES)
SEPARATED_LETTERS = re.compile(r"(?<![\w])(?:[^\W\d_][.\-\s]){3,}[^\W\d_](?![\w])")


def _join(match: re.Match) -> str:
    return re.sub(r"[.\-\s]", "", match.group(0))


def defend(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(character for character in text if unicodedata.category(character) != "Cf")
    text = text.translate(TRANSLATION)
    return SEPARATED_LETTERS.sub(_join, text)
