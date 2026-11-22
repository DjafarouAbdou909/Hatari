import pytest

from hatari.analysis.risk import (
    CRITICAL, HIGH, LOW, MODERATE, assess, categorize, language, recommendations, warnings,
)
from hatari.analysis.signals import Signal, detect


def signal(id_, strength):
    return Signal(id_, id_, "", strength, ("x",))


def category_ids(text):
    return [category.id for category in categorize(detect(text))]


def test_score_adds_model_and_capped_signal_points():
    risk = assess(0.5, [signal("a", "strong"), signal("b", "strong"), signal("c", "strong"), signal("d", "weak")])
    assert risk.model_points == 25.0
    assert risk.signal_points == 50
    assert risk.score == 75


@pytest.mark.parametrize("model_score, strengths, level", [
    (0.0, [], LOW),
    (0.4, ["weak"], MODERATE),
    (1.0, [], HIGH),
    (1.0, ["strong"], HIGH),
    (0.9, ["strong", "strong"], CRITICAL),
    (0.0, ["strong", "strong", "medium"], HIGH),
])
def test_levels(model_score, strengths, level):
    signals = [signal(f"s{i}", strength) for i, strength in enumerate(strengths)]
    assert assess(model_score, signals).level == level


def test_critical_requires_two_strong_signals():
    risk = assess(1.0, [signal("a", "strong"), signal("b", "medium"), signal("c", "medium")])
    assert risk.score >= 75
    assert risk.level == HIGH


def test_assess_rejects_scores_outside_the_unit_interval():
    with pytest.raises(ValueError):
        assess(1.5, [])


def test_advance_fee_example_is_categorised():
    text = ("Félicitations ! Vous venez de gagner 250 000 FCFA. Pour recevoir votre argent, envoyez immédiatement "
            "2 000 FCFA de frais au numéro indiqué.")
    assert category_ids(text)[0] == "advance_fee"


@pytest.mark.parametrize("text, expected", [
    ("Orange Money : 50 000 FCFA reçus par erreur. Renvoyez le montant au 0707070707.", "mobile_money_scam"),
    ("Votre compte sera suspendu. Communiquez votre code PIN par retour de SMS.", "credential_theft"),
    ("Your account is locked, verify your account at http://bit.ly/abc", "phishing"),
    ("Recrutement : poste à pourvoir. Payez les frais de dossier de 5 000 FCFA.", "fake_recruitment"),
    ("Investissez et gagnez 5 % par jour, rendement garanti.", "investment_scam"),
])
def test_first_category(text, expected):
    assert category_ids(text)[0] == expected


def test_no_category_is_forced_without_evidence():
    assert category_ids("Bonjour, la réunion est à 10 h demain.") == ["unclassified"]


def test_language_guess():
    assert language("Your account is locked, call us now") == "en"
    assert language("Votre compte est bloqué, appelez le service") == "fr"
    assert language("12345") == "unknown"


def test_warnings_for_short_and_non_english_messages():
    assert len(warnings("Salut")) == 2
    assert warnings("I will call you later tonight when I am back home from work") == []


def test_low_risk_recommendation_never_claims_safety():
    text = " ".join(recommendations(LOW, categorize([])))
    assert "ne garantit pas" in text
