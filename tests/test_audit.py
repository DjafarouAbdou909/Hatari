import pandas as pd

from hatari.data.audit import exact_key, overlap, split_leakage, template_key


def test_exact_key_ignores_case_spacing_and_punctuation():
    assert exact_key("Call NOW!!  0800-123") == exact_key("call now 0800123")
    assert exact_key("Félicitations") != exact_key("Felicitations")


def test_template_key_masks_digits_only():
    assert template_key("Dossier Lyon-1000") == template_key("Dossier Lyon-1001")
    assert template_key("Envoyez 2000 FCFA") == template_key("Envoyez 500 FCFA")
    assert template_key("Envoyez 2000 FCFA") != template_key("Recevez 2000 FCFA")


def _frame(texts, labels, splits=None):
    frame = pd.DataFrame({"text": texts, "original_label": labels, "suspicious": [l != "ham" for l in labels]})
    if splits is not None:
        frame["published_split"] = splits
    return frame


def test_overlap_counts_shared_texts_once():
    first = _frame(["Hello you", "hello you", "Win cash"], ["ham", "ham", "spam"])
    second = _frame(["HELLO YOU", "Verify account"], ["ham", "smishing"])

    result = overlap(first, second)

    assert result["shared_texts"] == 1
    assert result["only_first"] == 1
    assert result["only_second"] == 1


def test_split_leakage_detects_templates_across_splits():
    frame = _frame(["Code 1234", "Code 9876", "Bonjour"], ["spam", "spam", "ham"], ["train", "test", "test"])

    result = split_leakage(frame)

    assert result == {"texts_in_several_splits": 0, "templates_in_several_splits": 1}
