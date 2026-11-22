import numpy as np
import pandas as pd

from hatari.models.candidates import Candidate, all_candidates, build, decision_scores
from hatari.models.selection import fold_assignment, metrics, select


def _results(rows):
    return pd.DataFrame([{"candidate": name, "language": "en", "f1": f1, "recall": recall} for name, f1, recall in rows])


def test_select_prefers_recall_among_equivalent_f1():
    candidates = [Candidate("LR", "normalize", 1.0), Candidate("SVM", "normalize", 1.0)]
    results = _results([("LR_normalize_C1", 0.900, 0.80), ("SVM_normalize_C1", 0.905, 0.85)])
    assert select(results, candidates).name == "SVM_normalize_C1"


def test_select_prefers_the_simpler_candidate_when_f1_and_recall_tie():
    candidates = [Candidate("NB", "normalize"), Candidate("LR-char", "mask", 10.0)]
    results = _results([("NB_normalize", 0.900, 0.850), ("LR-char_mask_C10", 0.909, 0.855)])
    assert select(results, candidates).name == "NB_normalize"


def test_select_keeps_a_clearly_better_f1():
    candidates = [Candidate("NB", "normalize"), Candidate("LR", "mask", 1.0)]
    results = _results([("NB_normalize", 0.80, 0.95), ("LR_mask_C1", 0.90, 0.85)])
    assert select(results, candidates).name == "LR_mask_C1"


def test_fold_assignment_keeps_groups_whole():
    frame = pd.DataFrame({"language": ["en"] * 40, "group": [i // 4 for i in range(40)],
                          "suspicious": [i % 8 < 4 for i in range(40)]})
    folds = fold_assignment(frame)
    assert frame.assign(fold=folds).groupby("group")["fold"].nunique().max() == 1
    assert set(folds) == {0, 1, 2, 3, 4}


def test_metrics_counts_the_confusion_matrix():
    result = metrics([True, True, False, False], [0.9, 0.2, 0.7, 0.1], threshold=0.5)
    assert (result["true_positives"], result["false_negatives"], result["false_positives"],
            result["true_negatives"]) == (1, 1, 1, 1)
    assert result["precision"] == 0.5 and result["recall"] == 0.5


def test_every_candidate_trains_and_scores():
    texts = ["WIN cash now call 0800123456", "see you at lunch", "claim your prize at www.win.com",
             "ok i will call you later", "Urgent: verify your account", "thanks for the meeting"] * 3
    labels = [True, False, True, False, True, False] * 3
    for candidate in all_candidates():
        model = build(candidate).fit(texts, labels)
        assert np.isfinite(decision_scores(model, ["free prize now"])).all()
