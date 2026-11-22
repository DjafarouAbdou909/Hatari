from hatari.data.cleaning import has_generator_marker, strip_generator_markers


def test_strips_the_legitimate_reference_marker():
    text = "Le train a quelques minutes de retard. Merci, à bientôt. [référence SM-00005]"
    assert strip_generator_markers(text) == "Le train a quelques minutes de retard. Merci, à bientôt."


def test_strips_the_spam_file_marker_in_the_middle_of_a_message():
    text = "Ouvrez la page sécurisée pour confirmer vos données. Dossier Saint-Étienne-1000. Merci de ne jamais communiquer votre code"
    assert strip_generator_markers(text) == ("Ouvrez la page sécurisée pour confirmer vos données. "
                                             "Merci de ne jamais communiquer votre code")


def test_leaves_ordinary_text_unchanged():
    text = "Votre dossier 1234 est prêt. Envoyez 2 000 FCFA au 07 00 00 00 00."
    assert strip_generator_markers(text) == text
    assert not has_generator_marker(text)
