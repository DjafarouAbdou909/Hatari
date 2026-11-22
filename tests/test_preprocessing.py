import pytest

from hatari.text.preprocessing import (
    EMAIL_TOKEN, MONEY_TOKEN, PHONE_TOKEN, URL_TOKEN, InvalidMessage, mask_entities, normalize, validate_message,
)


def test_normalize_decodes_html_entities_and_collapses_spaces():
    assert normalize("I'll be there &lt;#&gt;   mins\n ok") == "I'll be there <#> mins ok"


def test_normalize_keeps_case_digits_and_symbols():
    assert normalize("WIN £1000 now 0800") == "WIN £1000 now 0800"


@pytest.mark.parametrize("text, expected", [
    ("Envoyez 2 000 FCFA au 07 08 09 10 11", f"Envoyez {MONEY_TOKEN} au {PHONE_TOKEN}"),
    ("Vous avez gagné 250.000 F CFA", f"Vous avez gagné {MONEY_TOKEN}"),
    ("Claim £1000 cash, call 09061701461", f"Claim {MONEY_TOKEN} cash, call {PHONE_TOKEN}"),
    ("entitled to 3750 pounds for the accident", f"entitled to {MONEY_TOKEN} for the accident"),
    ("Appelez le +225 07 00 00 00 00", f"Appelez le {PHONE_TOKEN}"),
    ("Visit http://bit.ly/abc?x=1 now", f"Visit {URL_TOKEN} now"),
    ("Allez sur orange-money-ci.com/verif", f"Allez sur {URL_TOKEN}"),
    ("Écrivez à support@banque.ci", f"Écrivez à {EMAIL_TOKEN}"),
])
def test_mask_entities(text, expected):
    assert mask_entities(text) == expected


def test_mask_entities_leaves_times_and_short_numbers():
    assert mask_entities("RDV à 12 h 40, salle 3") == "RDV à 12 h 40, salle 3"


@pytest.mark.parametrize("value", [None, 42, "", "   ", "a" * 5001])
def test_validate_message_rejects_unusable_input(value):
    with pytest.raises(InvalidMessage):
        validate_message(value)


def test_validate_message_accepts_text():
    assert validate_message("Bonjour") == "Bonjour"
