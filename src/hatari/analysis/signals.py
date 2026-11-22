"""Rule-based fraud signals of docs/07_risk_methodology.md.

Patterns are matched on a folded copy of the message, lower-cased and without
accents, which has exactly the same length as the message. The evidence of a
signal is therefore always an excerpt of the original text, as the user wrote it.
Labels and explanations are in French, the language of the interface.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from hatari.text.preprocessing import EMAIL, MONEY, PHONE, URL, normalize

STRONG, MEDIUM, WEAK = "strong", "medium", "weak"
MAX_EVIDENCE = 3
NEGATION_WINDOW = 40

MONEY_WORDS = r"(?:argent|frais|montant|somme|f ?cfa|cfa|francs?|xof|money|cash|fees?|\$|£|€|\b\d{3,6}\b)"
NEAR = r"\W+(?:[\w'’-]+\W+){0,6}?"


@dataclass(frozen=True)
class SignalDefinition:
    id: str
    label: str
    explanation: str
    strength: str
    patterns: tuple[re.Pattern, ...]
    negatable: bool = False


@dataclass(frozen=True)
class Signal:
    id: str
    label: str
    explanation: str
    strength: str
    evidence: tuple[str, ...]


def _compile(*patterns: str) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


def fold(text: str) -> str:
    """Lower-case and remove accents, keeping one character for each character of the text."""
    folded = []
    for character in text:
        base = unicodedata.normalize("NFKD", character)[0].lower()
        folded.append(base[0] if base else character)
    return "".join(folded)


DEFINITIONS: tuple[SignalDefinition, ...] = (
    SignalDefinition(
        "money_request", "Demande d'argent ou de frais",
        "Le message demande d'envoyer, de payer ou de déposer de l'argent.", STRONG,
        _compile(
            rf"\b(?:envoy|renvoy|transfer|transfe|pay|verse|depos|recharg|rembours|send|wire|remit|refund)\w*{NEAR}{MONEY_WORDS}",
            r"\bfrais (?:de |d'|d’)\s?(?:dossier|inscription|transfert|livraison|activation|traitement|deblocage|"
            r"retrait|liberation|douane|validation)",
            r"\b(?:processing|release|clearance|registration|activation|delivery|small|transfer) fee",
            r"\badvance fee\b",
        )),
    SignalDefinition(
        "credential_request", "Demande de code, de PIN ou de mot de passe",
        "Le message demande de communiquer un code secret, un PIN, un mot de passe ou des identifiants.", STRONG,
        _compile(
            r"\b(?:communiqu|envoy|donn|transmet|partag|saisi|entrez|tapez|composez|send|share|give|enter|"
            r"reply with|provide|confirm)\w*" + NEAR +
            r"(?:code|pin|mot de passe|password|otp|identifiants|login|cvv|numero de (?:la )?carte|card number)\b",
            r"\b(?:code|pin|mot de passe|password|otp|identifiants|cvv)\b" + NEAR +
            r"(?:par (?:retour|sms|message)|en reponse|to (?:this|us)|by (?:sms|reply))",
        ),
        negatable=True),
    SignalDefinition(
        "account_threat", "Menace sur un compte",
        "Le message annonce qu'un compte, une carte ou une ligne va être bloqué, suspendu ou fermé.", STRONG,
        _compile(
            r"\b(?:compte|account|carte|card|ligne|sim|acces|access)" + NEAR +
            r"(?:suspendu|bloque|desactive|ferme|restreint|suspended|blocked|locked|disabled|closed|restricted|"
            r"deactivated)",
            r"\b(?:suspension|blocage|fermeture|desactivation) (?:de |d')?(?:votre |ton |your )?"
            r"(?:compte|ligne|carte|account|line|card)\b",
            r"\b(?:verif|confirm|mettre a jour|mettez a jour|update|reactiv|debloqu|unlock)\w*\W+"
            r"(?:\w+\W+){0,2}?(?:votre |your )?(?:compte|account|identite|identity)\b",
        )),
    SignalDefinition(
        "shortened_link", "Lien raccourci ou masqué",
        "Le message contient un lien raccourci ou une adresse IP, qui cachent la vraie destination.", STRONG,
        _compile(
            r"\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly|is\.gd|cutt\.ly|rb\.gy|shorturl\.at|tiny\.cc|"
            r"t\.ly|s\.id)/\S*",
            r"https?://\d{1,3}(?:\.\d{1,3}){3}\S*",
        )),
    SignalDefinition(
        "mistaken_transfer", "Transfert « par erreur »",
        "Le message prétend qu'un transfert a été fait par erreur, un procédé courant pour se faire renvoyer de l'argent.",
        STRONG,
        _compile(r"\b(?:par erreur|by mistake|sent (?:you )?\w* ?by mistake|wrongly sent|mauvais numero)\b")),
    SignalDefinition(
        "prize_promise", "Promesse de gain ou de prix",
        "Le message annonce un gain, un prix ou une sélection inattendus.", MEDIUM,
        _compile(
            r"\b(?:felicitations|vous avez (?:ete )?(?:gagne|selectionne|tire)|vous gagnez|gagnant|loterie|tombola|"
            r"tirage au sort|congratulations|you (?:have )?(?:won|been selected)|winner|prize|awarded|claim your|"
            r"cadeau gratuit|free gift)\b",
            r"\b(?:vous|tu) (?:venez de |avez |as )?(?:gagner|gagne|remporter|remporte)\b",
            r"\b(?:you (?:have )?just won|you have won)\b",
            r"(?:(?<=\d)|\b)(?:million|milion|milliard|billion)s?\s*(?:de\s+)?(?:dollars?|euros?|usd|f ?cfa|francs?|pounds?)\b",
            r"\b(?:to transfer to you|vous transferer|en votre faveur|in your favou?r|inheritance|heritage|"
            r"beneficiary|beneficiaire)\b",
        )),
    SignalDefinition(
        "urgency", "Urgence artificielle",
        "Le message pousse à agir vite, ce qui empêche de vérifier.", MEDIUM,
        _compile(
            r"\b(?:urgent|immediatement|tout de suite|sans delai|des maintenant|dernier (?:delai|rappel|avertissement)|"
            r"avant (?:ce soir|minuit)|offre limitee|right now|immediately|asap|last chance|final (?:notice|warning)|"
            r"today only|act now|expires? (?:today|soon|in)|expire (?:aujourd'hui|bientot|dans))\b",
            r"\b(?:dans|sous|pendant|valable|within|in the next) (?:les? )?\d+ ?(?:h|heures?|minutes?|mn|min|hours?|hrs?|"
            r"mins?)\b",
        )),
    SignalDefinition(
        "mobile_money", "Contexte Mobile Money",
        "Le message parle d'un service de Mobile Money.", MEDIUM,
        _compile(
            r"\b(?:orange money|mtn (?:mobile )?money|momo|moov (?:africa )?money|flooz|mobile money|m-?pesa|"
            r"airtel money|(?:compte|par|via|sur) wave|wave (?:ci|mobile money))\b",
        )),
    SignalDefinition(
        "job_offer", "Offre d'emploi",
        "Le message propose un emploi ou un revenu.", MEDIUM,
        _compile(
            r"\b(?:recrutement|recrute|offre d'emploi|poste a pourvoir|travail a domicile|salaire|job offer|"
            r"we are hiring|vacancy|recruitment|work from home|part[ -]time job|salary)\b",
        )),
    SignalDefinition(
        "investment_promise", "Promesse d'investissement",
        "Le message promet un rendement ou un profit sur un placement.", MEDIUM,
        _compile(
            r"\b(?:investissement|investissez|rendement garanti|doublez votre|doubler votre|crypto\w*|bitcoin|forex|"
            r"guaranteed (?:returns?|profits?)|double your|investment)\b",
            r"\b\d+ ?% (?:par|per|a|chaque) (?:jour|day|semaine|week|mois|month)\b",
        )),
    SignalDefinition(
        "institution", "Se présente comme une institution",
        "Le message se réclame d'une banque, d'un opérateur ou d'un service officiel. Son authenticité ne peut pas être "
        "vérifiée à partir du texte.", MEDIUM,
        _compile(
            r"\b(?:service client(?:ele)?|customer (?:care|service|support)|votre banque|your bank|orange ci|"
            r"orange money|mtn|moov|tresor public|impots|police|gendarmerie|ministere|douane|paypal|apple id|netflix|"
            r"dhl|fedex|western union|moneygram)\b",
        )),
    SignalDefinition(
        "link", "Lien internet", "Le message contient une adresse internet.", WEAK,
        (re.compile(r"(?<![@\w.-])(?:" + URL.pattern + ")", re.IGNORECASE),)),
    SignalDefinition(
        "email_address", "Adresse e-mail", "Le message invite à écrire à une adresse e-mail.", WEAK, (EMAIL,)),
    SignalDefinition(
        "phone_number", "Numéro de téléphone", "Le message contient un numéro de téléphone.", WEAK, (PHONE,)),
    SignalDefinition(
        "amount", "Montant d'argent", "Le message mentionne une somme d'argent.", WEAK, (MONEY,)),
)

BY_ID = {definition.id: definition for definition in DEFINITIONS}
NEGATION = re.compile(r"\b(?:ne\b.{0,25}\bjamais|jamais|never|do not|don't|n'?\s?(?:envoyez|communiquez|partagez|donnez))",
                      re.IGNORECASE)


def _negated(folded: str, start: int) -> bool:
    return bool(NEGATION.search(folded[max(0, start - NEGATION_WINDOW):start]))


def detect(text: str) -> list[Signal]:
    """Return the signals found in a message, in the order of DEFINITIONS, with their evidence."""
    original = normalize(text)
    folded = fold(original)
    found = []
    for definition in DEFINITIONS:
        evidence = []
        for pattern in definition.patterns:
            for match in pattern.finditer(folded):
                if definition.negatable and _negated(folded, match.start()):
                    continue
                excerpt = original[match.start():match.end()].strip()
                if excerpt and excerpt not in evidence:
                    evidence.append(excerpt)
        if evidence:
            found.append(Signal(definition.id, definition.label, definition.explanation, definition.strength,
                                tuple(evidence[:MAX_EVIDENCE])))
    return found
