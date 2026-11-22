"""Text normalisation shared by training and inference.

The same functions must run on training data and on user messages, otherwise
the model would see different inputs in production. Two levels are provided.

- ``normalize`` only repairs the encoding. It applies Unicode NFKC
  normalisation, decodes HTML entities such as ``&lt;``, which leak the label in
  the UCI data, applies the obfuscation defence of ``hatari.text.defence``,
  adopted on 22 November 2026 after docs/research_obfuscation_results.md, and
  collapses whitespace. It keeps case, digits, links and
  currency symbols, which are fraud signals.
- ``mask_entities`` additionally replaces each link, email address, phone number
  and money amount by a placeholder token. Whether this helps the model to
  generalise across countries is decided by the model comparison.
"""

from __future__ import annotations

import html
import re
import unicodedata

from .defence import defend

MAX_CHARACTERS = 5000

URL_TOKEN, EMAIL_TOKEN, PHONE_TOKEN, MONEY_TOKEN = "xurlx", "xemailx", "xphonex", "xmoneyx"

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
URL = re.compile(
    r"\b(?:https?://|www\.)\S+"
    r"|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|info|biz|ly|co|ci|fr|uk|me|io|xyz|top|online|site)(?:/\S*)?\b",
    re.IGNORECASE,
)
CURRENCY = r"(?:fcfa|f\s?cfa|cfa|xof|francs?|eur|euros?|usd|dollars?|pounds?|gbp|inr|£|\$|€)"
AMOUNT = r"\d{1,3}(?:[ ., ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
MONEY = re.compile(rf"(?:{CURRENCY}\s?(?:{AMOUNT})|(?:{AMOUNT})\s?{CURRENCY})(?![\w])", re.IGNORECASE)
PHONE = re.compile(r"(?<![\w])\+?\d(?:[\s.-]?\d){7,13}(?![\w])")


class InvalidMessage(ValueError):
    """Raised when a message cannot be analysed."""


def validate_message(text: object, max_characters: int = MAX_CHARACTERS) -> str:
    """Return the message if it can be analysed, otherwise raise InvalidMessage."""
    if not isinstance(text, str):
        raise InvalidMessage("Le message doit être du texte.")
    if not text.strip():
        raise InvalidMessage("Le message est vide.")
    if len(text) > max_characters:
        raise InvalidMessage(f"Le message dépasse {max_characters} caractères.")
    return text


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = html.unescape(text)
    text = defend(text)
    return re.sub(r"\s+", " ", text).strip()


def mask_entities(text: str) -> str:
    """Replace emails, links, money amounts and phone numbers by placeholder tokens, in that order."""
    text = normalize(text)
    text = EMAIL.sub(f" {EMAIL_TOKEN} ", text)
    text = URL.sub(f" {URL_TOKEN} ", text)
    text = MONEY.sub(f" {MONEY_TOKEN} ", text)
    text = PHONE.sub(f" {PHONE_TOKEN} ", text)
    return re.sub(r"\s+", " ", text).strip()
