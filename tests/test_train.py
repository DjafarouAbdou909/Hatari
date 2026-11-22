import numpy as np
import pandas as pd

from hatari.models.train import fit, grouped_splits


def _frame():
    suspicious = [f"WIN a prize of {i} pounds, call 0800{i:06d} now" for i in range(15)]
    legitimate = [f"See you at {i} for lunch with the team" for i in range(15)]
    return pd.DataFrame({"text": suspicious + legitimate, "suspicious": [True] * 15 + [False] * 15,
                         "language": "en", "group": [f"s{i}" for i in range(15)] + [f"l{i}" for i in range(15)]})


def test_grouped_splits_cover_every_row_once_as_held_out():
    splits = grouped_splits(_frame())
    held = np.concatenate([test for _, test in splits])
    assert sorted(held) == list(range(30))
    for train, test in splits:
        assert not set(train) & set(test)


def test_fit_returns_calibrated_probabilities():
    model = fit(_frame())
    probabilities = model.predict_proba(["claim your prize now call 0800123456", "lunch with the team at noon"])[:, 1]
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    assert probabilities[0] > probabilities[1]
