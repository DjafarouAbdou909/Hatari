import pandas as pd
import pytest

from hatari.data.corpus import TEST, TRAIN, assign_english_split, english_corpus, french_corpus


def _source(name, texts, labels):
    return pd.DataFrame({"source": name, "row": range(1, len(texts) + 1), "language": "en", "origin": "real",
                         "channel": "sms", "text": texts, "original_label": labels,
                         "suspicious": [label != "ham" for label in labels]})


def test_english_corpus_merges_shared_texts_and_keeps_the_uci_text():
    uci = _source("uci_sms_spam", ["Call me later", "WIN cash now"], ["ham", "spam"])
    mendeley = _source("mendeley_smishing", ["call me later�", "Verify your bank account"], ["ham", "smishing"])

    corpus = english_corpus(uci, mendeley)

    assert len(corpus) == 3
    shared = corpus[corpus["sources"] == "mendeley_smishing+uci_sms_spam"]
    assert shared["text"].tolist() == ["Call me later"]


def test_english_corpus_rejects_conflicting_binary_labels():
    uci = _source("uci_sms_spam", ["Hello"], ["ham"])
    mendeley = _source("mendeley_smishing", ["hello!"], ["spam"])

    with pytest.raises(ValueError):
        english_corpus(uci, mendeley)


def test_english_split_keeps_each_template_on_one_side():
    texts = [f"Your code is {i}" for i in range(20)] + [f"Message number {chr(97 + i)}" for i in range(20)]
    labels = ["spam"] * 20 + ["ham"] * 20
    corpus = english_corpus(_source("uci_sms_spam", texts, labels), _source("mendeley_smishing", [], []))

    split = assign_english_split(corpus)

    assert set(split) <= {TRAIN, TEST}
    assert corpus.assign(split=split).groupby("group")["split"].nunique().max() == 1
    assert corpus.loc[corpus["text"].str.startswith("Your code"), "group"].nunique() == 1


def test_french_corpus_moves_validation_into_training():
    synthetic = pd.DataFrame({"source": "french_synthetic", "text": ["a", "b", "c"],
                              "published_split": ["train", "validation", "test"],
                              "template_group": ["g1", "g2", "g3"]})

    corpus = french_corpus(synthetic)

    assert corpus["split"].tolist() == [TRAIN, TRAIN, TEST]
    assert corpus["group"].tolist() == ["g1", "g2", "g3"]
