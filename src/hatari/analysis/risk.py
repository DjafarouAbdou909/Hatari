"""Threat categories, risk score and recommendations of docs/07_risk_methodology.md."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .signals import MEDIUM, STRONG, WEAK, Signal

MODEL_POINTS = 50
SIGNAL_POINTS_CAP = 50
POINTS = {STRONG: 20, MEDIUM: 10, WEAK: 5}
SHORT_MESSAGE = 40

LOW, MODERATE, HIGH, CRITICAL = "low", "moderate", "high", "critical"
LEVEL_LABELS = {LOW: "Risque faible", MODERATE: "Risque modéré", HIGH: "Risque élevé", CRITICAL: "Risque critique"}


@dataclass(frozen=True)
class Category:
    id: str
    label: str


CATEGORY_RULES: tuple[tuple[Category, object], ...] = (
    (Category("credential_theft", "Vol de codes ou d'identifiants"),
     lambda s: "credential_request" in s),
    (Category("mobile_money_scam", "Arnaque au Mobile Money"),
     lambda s: "mobile_money" in s and bool(s & {"money_request", "credential_request", "mistaken_transfer"})),
    (Category("advance_fee", "Arnaque aux frais avancés"),
     lambda s: "prize_promise" in s and "money_request" in s),
    (Category("phishing", "Hameçonnage"),
     lambda s: "account_threat" in s and bool(s & {"link", "shortened_link", "credential_request"})),
    (Category("fake_recruitment", "Faux recrutement"),
     lambda s: "job_offer" in s and "money_request" in s),
    (Category("investment_scam", "Investissement suspect"),
     lambda s: "investment_promise" in s),
    (Category("impersonation", "Usurpation d'identité possible"),
     lambda s: "institution" in s and bool(s & {"money_request", "credential_request", "account_threat"})),
    (Category("prize_scam", "Faux gain ou fausse loterie"),
     lambda s: "prize_promise" in s and "money_request" not in s),
    (Category("suspicious_link", "Lien suspect"),
     lambda s: "shortened_link" in s),
    (Category("social_engineering", "Manipulation psychologique"),
     lambda s: "urgency" in s and bool(s & {"money_request", "credential_request", "account_threat", "link",
                                            "shortened_link", "phone_number", "email_address"})),
)
UNCLASSIFIED = Category("unclassified", "Non classé")

RECOMMENDATIONS = {
    "credential_theft": "Ne communiquez jamais un code secret, un PIN ou un mot de passe, même à quelqu'un qui se dit agent.",
    "mobile_money_scam": "Vérifiez votre solde directement dans l'application ou le menu officiel de votre opérateur, "
                         "jamais à partir du message.",
    "advance_fee": "N'envoyez aucun frais pour recevoir un gain. Un vrai gain ne demande pas de payer d'avance.",
    "phishing": "N'ouvrez pas le lien. Connectez-vous à votre compte uniquement par l'application ou le site officiel.",
    "fake_recruitment": "Un employeur sérieux ne demande pas de payer pour obtenir un poste.",
    "investment_scam": "Méfiez-vous de tout rendement garanti ou très élevé. Renseignez-vous auprès d'un organisme agréé.",
    "impersonation": "Contactez l'institution par son numéro officiel, pas par celui donné dans le message.",
    "prize_scam": "Vérifiez le gain auprès de l'organisateur par un canal officiel avant toute démarche.",
    "suspicious_link": "N'ouvrez pas un lien raccourci ou masqué dont vous ne connaissez pas la destination.",
    "social_engineering": "Prenez le temps de vérifier. L'urgence est un moyen d'empêcher la réflexion.",
}
GENERAL_RECOMMENDATIONS = {
    LOW: ["Aucun signal important n'a été trouvé, mais cela ne garantit pas que le message est sûr.",
          "En cas de doute, vérifiez l'expéditeur par un autre moyen."],
    MODERATE: ["Vérifiez l'expéditeur par un canal officiel avant de répondre.",
               "Ne partagez aucune information personnelle ou financière."],
    HIGH: ["N'envoyez pas d'argent et ne partagez aucune information confidentielle.",
           "Vérifiez auprès de l'organisme concerné par un canal officiel."],
    CRITICAL: ["N'envoyez pas d'argent et ne partagez aucune information confidentielle.",
               "Ne rappelez pas le numéro et n'ouvrez pas les liens du message.",
               "Bloquez et signalez l'expéditeur si la fraude se confirme."],
}

ENGLISH_WORDS = {"the", "you", "your", "to", "and", "is", "for", "of", "are", "have", "this", "now", "will", "with",
                 "call", "be", "it", "me", "my", "i", "on", "at", "get", "can", "just"}
FRENCH_WORDS = {"le", "la", "les", "vous", "votre", "vos", "de", "des", "du", "et", "est", "pour", "un", "une", "sur",
                "au", "aux", "ne", "pas", "je", "tu", "nous", "avec", "ce", "dans", "par", "qui", "que", "mon", "ma"}


@dataclass(frozen=True)
class Risk:
    score: int
    level: str
    level_label: str
    model_points: float
    signal_points: int
    strong_signals: int


def categorize(signals: list[Signal]) -> list[Category]:
    present = {signal.id for signal in signals}
    categories = [category for category, rule in CATEGORY_RULES if rule(present)]
    return categories or [UNCLASSIFIED]


def assess(model_score: float, signals: list[Signal]) -> Risk:
    if not 0.0 <= model_score <= 1.0:
        raise ValueError(f"model score {model_score} outside [0, 1]")
    model_points = MODEL_POINTS * model_score
    signal_points = min(SIGNAL_POINTS_CAP, sum(POINTS[signal.strength] for signal in signals))
    score = int(round(model_points + signal_points))
    strong = sum(signal.strength == STRONG for signal in signals)
    if score >= 75 and strong >= 2:
        level = CRITICAL
    elif score >= 50:
        level = HIGH
    elif score >= 25:
        level = MODERATE
    else:
        level = LOW
    return Risk(score, level, LEVEL_LABELS[level], round(model_points, 1), signal_points, strong)


def language(text: str) -> str:
    """Rough language guess from frequent function words: ``en``, ``fr`` or ``unknown``."""
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", text.lower())
    english = sum(word in ENGLISH_WORDS for word in words)
    french = sum(word in FRENCH_WORDS for word in words)
    if english == french:
        return "unknown"
    return "en" if english > french else "fr"


def warnings(text: str) -> list[str]:
    result = []
    if len(text.strip()) < SHORT_MESSAGE:
        result.append("Message très court : l'analyse dispose de peu d'éléments et elle est moins fiable.")
    if language(text) != "en":
        result.append("Le modèle a été entraîné surtout sur des messages en anglais et sur peu de messages français, "
                      "tous synthétiques. Son avis sur ce message est moins fiable, et des messages légitimes au ton "
                      "formel peuvent être jugés suspects.")
    return result


def recommendations(level: str, categories: list[Category]) -> list[str]:
    specific = [RECOMMENDATIONS[category.id] for category in categories if category.id in RECOMMENDATIONS]
    return specific + GENERAL_RECOMMENDATIONS[level]
