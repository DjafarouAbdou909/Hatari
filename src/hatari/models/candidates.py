"""Candidate classifiers of docs/04_modelling_protocol.md."""

from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from hatari.text.preprocessing import mask_entities, normalize

FAMILIES = ["NB", "LR", "SVM", "LR-char", "SVM-char"]
PREPROCESSINGS = ["normalize", "mask"]
C_GRID = [0.1, 1.0, 10.0]
SEED = 20261122


def lower_normalized(text: str) -> str:
    return normalize(text).lower()


def lower_masked(text: str) -> str:
    return mask_entities(text).lower()


PREPROCESSORS = {"normalize": lower_normalized, "mask": lower_masked}


@dataclass(frozen=True)
class Candidate:
    family: str
    preprocessing: str
    c: float | None = None
    name: str = field(init=False)

    def __post_init__(self):
        suffix = "" if self.c is None else f"_C{self.c:g}"
        object.__setattr__(self, "name", f"{self.family}_{self.preprocessing}{suffix}")

    @property
    def simplicity_rank(self) -> tuple[int, int, float]:
        """Lower is simpler, in the order of the protocol, then the stronger regularisation."""
        return FAMILIES.index(self.family), PREPROCESSINGS.index(self.preprocessing), self.c or 0.0


def word_features(preprocessing: str) -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=PREPROCESSORS[preprocessing], ngram_range=(1, 2), sublinear_tf=True)


def char_features(preprocessing: str) -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=PREPROCESSORS[preprocessing], analyzer="char_wb", ngram_range=(2, 5),
                           sublinear_tf=True, min_df=2)


def build(candidate: Candidate) -> Pipeline:
    if candidate.family.endswith("-char"):
        features = FeatureUnion([("word", word_features(candidate.preprocessing)),
                                 ("char", char_features(candidate.preprocessing))])
    else:
        features = word_features(candidate.preprocessing)
    if candidate.family == "NB":
        classifier = MultinomialNB()
    elif candidate.family.startswith("LR"):
        classifier = LogisticRegression(C=candidate.c, class_weight="balanced", max_iter=5000)
    else:
        classifier = LinearSVC(C=candidate.c, class_weight="balanced", random_state=SEED)
    return Pipeline([("features", features), ("classifier", classifier)])


def all_candidates() -> list[Candidate]:
    candidates = []
    for family in FAMILIES:
        for preprocessing in PREPROCESSINGS:
            grid = [None] if family == "NB" else C_GRID
            candidates.extend(Candidate(family, preprocessing, c) for c in grid)
    return candidates


def decision_scores(model: Pipeline, texts) -> "numpy.ndarray":
    """Probability of the suspicious class, or the SVM margin, for which the threshold is 0."""
    classifier = model.named_steps["classifier"]
    if hasattr(classifier, "predict_proba"):
        return model.predict_proba(texts)[:, 1]
    return model.decision_function(texts)


def default_threshold(candidate: Candidate) -> float:
    return 0.0 if candidate.family.startswith("SVM") else 0.5
