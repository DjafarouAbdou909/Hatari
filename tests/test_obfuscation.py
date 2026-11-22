import numpy as np
import pandas as pd

from hatari.research.obfuscation import CYRILLIC, ZERO_WIDTH_SPACE, perturb, perturbed_texts
from hatari.text.defence import defend


def test_defence_reverses_look_alikes_and_invisible_characters():
    rng = np.random.default_rng(0)
    text = "Verify your account now at our office"
    for code in ["P1", "P2"]:
        assert defend(perturb(text, code, rng)) == text


def test_defence_joins_separated_letters():
    assert defend("Please v.e.r.i.f.y your a-c-c-o-u-n-t") == "Please verify your account"


def test_defence_keeps_ordinary_text_and_digits():
    for text in ["if u r a good friend", "Call 0800 123 456 now", "Le code 1234 expire", "U.S. office"]:
        assert defend(text) == text
    assert defend("c0de") == "c0de"


def test_perturbations_change_text_but_keep_length_or_letters():
    rng = np.random.default_rng(1)
    text = "Your account will be suspended, please verify immediately"
    homoglyphs = perturb(text, "P1", rng)
    assert len(homoglyphs) == len(text) and homoglyphs != text
    assert set(homoglyphs) - set(text) <= set(CYRILLIC.values())
    assert perturb(text, "P2", rng).replace(ZERO_WIDTH_SPACE, "") == text
    assert perturb(text, "P0", rng) == text


def test_only_suspicious_messages_are_perturbed_and_reproducibly():
    frame = pd.DataFrame({"text": ["verify your account now please", "see you at lunch today"],
                          "suspicious": [True, False]})
    first, second = perturbed_texts(frame), perturbed_texts(frame)
    for code in first:
        assert first[code].equals(second[code])
        assert first[code].iloc[1] == "see you at lunch today"
