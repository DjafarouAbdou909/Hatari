import pytest

from hatari.analysis.signals import DEFINITIONS, detect, fold


def ids(text):
    return {signal.id for signal in detect(text)}


def test_fold_keeps_the_length_of_the_text():
    text = "Félicitations, À ÉTÉ reçu ! œuvre"
    assert len(fold(text)) == len(text)
    assert fold("Félicitations À") == "felicitations a"


def test_evidence_is_an_excerpt_of_the_original_text():
    text = "Félicitations ! Vous venez de gagner 250 000 FCFA."
    for signal in detect(text):
        for excerpt in signal.evidence:
            assert excerpt in text


def test_advance_fee_example_of_the_specification():
    text = ("Félicitations ! Vous venez de gagner 250 000 FCFA. Pour recevoir votre argent, envoyez immédiatement "
            "2 000 FCFA de frais au numéro indiqué. Offre valable pendant 10 minutes.")
    assert {"money_request", "prize_promise", "urgency", "amount"} <= ids(text)


@pytest.mark.parametrize("text, expected", [
    ("Orange Money : vous avez reçu 50 000 FCFA par erreur. Renvoyez le montant au 0707070707.",
     {"mistaken_transfer", "mobile_money", "money_request", "phone_number", "amount"}),
    ("Votre compte sera suspendu. Communiquez votre code PIN par retour de SMS.",
     {"credential_request", "account_threat"}),
    ("Recrutement : poste à pourvoir. Payez les frais de dossier de 5 000 FCFA.", {"job_offer", "money_request"}),
    ("Investissez 10 000 FCFA et gagnez 5 % par jour, rendement garanti.", {"investment_promise"}),
    ("Verify your account now at http://bit.ly/x1", {"account_threat", "shortened_link", "link"}),
    ("I have 7.3milion Dollar to transfer to you. Contact memea@gmail.com", {"prize_promise", "email_address"}),
])
def test_detects_fraud_patterns(text, expected):
    assert expected <= ids(text)


def test_a_warning_never_to_share_a_code_is_not_a_request():
    text = "Votre banque ne vous demandera jamais votre code PIN. Ne le communiquez à personne."
    assert "credential_request" not in ids(text)


def test_an_email_address_is_not_a_link():
    assert ids("Écrivez à support@banque.ci") == {"email_address"}


@pytest.mark.parametrize("text", [
    "Salut, on se retrouve à 18h devant le maquis ?",
    "Ok lar... Joking wif u oni...",
    "Je t'envoie le document ce soir, merci.",
])
def test_ordinary_messages_trigger_no_signal(text):
    assert ids(text) == set()


def test_every_definition_has_a_french_label_and_a_known_strength():
    for definition in DEFINITIONS:
        assert definition.label and definition.explanation
        assert definition.strength in {"strong", "medium", "weak"}


def test_a_phone_number_is_not_an_amount_requested():
    assert "money_request" not in ids("Envoyez votre code secret au 0707070707.")
    assert "money_request" in ids("Envoyez 5000 au numéro indiqué.")


def test_a_noun_announcing_suspension_is_an_account_threat():
    assert "account_threat" in ids("Merci de répondre afin d'éviter la suspension de votre ligne.")
