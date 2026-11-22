"""Prediction service: one message in, one structured and explained analysis out.

The analysis keeps four parts apart, as required by the specification:

- ``signals``, patterns observed in the text, each with its evidence;
- ``model``, the result of the machine learning classifier and the terms that weighed most in it;
- ``categories``, deduced from the signals by explicit rules;
- ``risk``, the final assessment that combines the model and the signals.

The message is never stored or logged by this module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import joblib
import numpy as np

from hatari.analysis.risk import Risk, assess, categorize, recommendations, warnings
from hatari.analysis.signals import Signal, detect
from hatari.models.train import METADATA_FILE, MODEL_FILE, MODELS_DIR, THRESHOLD
from hatari.text.preprocessing import EMAIL_TOKEN, MONEY_TOKEN, PHONE_TOKEN, URL_TOKEN, validate_message

TOP_TERMS = 5
TOKEN_LABELS = {PHONE_TOKEN: "[numéro]", MONEY_TOKEN: "[montant]", URL_TOKEN: "[lien]", EMAIL_TOKEN: "[e-mail]"}


class ModelNotFound(FileNotFoundError):
    """Raised when the trained model file is missing."""


@dataclass(frozen=True)
class ModelResult:
    score: float
    label: str
    summary: str
    suspicious_terms: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Analysis:
    risk: Risk
    model: ModelResult
    signals: list[Signal]
    categories: list[dict]
    explanation: list[str]
    recommendations: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def readable_term(term: str) -> str:
    for token, label in TOKEN_LABELS.items():
        term = term.replace(token, label)
    return term


class Analyzer:
    def __init__(self, models_dir: Path = MODELS_DIR):
        path = Path(models_dir) / MODEL_FILE
        if not path.exists():
            raise ModelNotFound(f"Modèle introuvable dans {path}. Lancez python -m hatari.models.train.")
        self.model = joblib.load(path)
        metadata_path = Path(models_dir) / METADATA_FILE
        self.metadata = metadata_path.read_text() if metadata_path.exists() else ""
        pipeline = self.model.calibrated_classifiers_[0].estimator
        self._features = pipeline.named_steps["features"]
        self._coefficients = pipeline.named_steps["classifier"].coef_.ravel()
        self._names = self._features.get_feature_names_out()

    def suspicious_terms(self, text: str, top: int = TOP_TERMS) -> list[str]:
        """Terms of the message whose weight pushed the linear model most towards suspicious."""
        row = self._features.transform([text]).tocsr()
        contributions = row.data * self._coefficients[row.indices]
        order = np.argsort(contributions)[::-1]
        terms = []
        for position in order:
            if contributions[position] <= 0 or len(terms) == top:
                break
            terms.append(readable_term(self._names[row.indices[position]]))
        return terms

    def model_result(self, text: str) -> ModelResult:
        score = float(self.model.predict_proba([text])[0, 1])
        suspicious = score > THRESHOLD
        label = "suspect" if suspicious else "non suspect"
        summary = ("La formulation ressemble davantage aux messages suspects des données d'entraînement."
                   if suspicious else
                   "La formulation ressemble davantage aux messages légitimes des données d'entraînement.")
        return ModelResult(round(score, 3), label, summary, self.suspicious_terms(text) if suspicious else [])

    def analyze(self, text: object) -> Analysis:
        message = validate_message(text)
        model = self.model_result(message)
        signals = detect(message)
        risk = assess(model.score, signals)
        categories = categorize(signals)
        explanation = explain(risk, model, signals)
        return Analysis(
            risk=risk, model=model, signals=signals,
            categories=[{"id": category.id, "label": category.label} for category in categories],
            explanation=explanation, recommendations=recommendations(risk.level, categories),
            warnings=warnings(message),
        )


def explain(risk: Risk, model: ModelResult, signals: list[Signal]) -> list[str]:
    """Plain French sentences that separate what is observed, what the model says and the final assessment."""
    sentences = []
    if signals:
        names = ", ".join(signal.label.lower() for signal in signals)
        sentences.append(f"Signaux observés dans le texte : {names}.")
    else:
        sentences.append("Aucun des signaux recherchés n'a été trouvé dans le texte.")
    sentences.append(f"Modèle d'apprentissage automatique : score de {model.score:.2f} sur 1. {model.summary}")
    sentences.append(
        f"Évaluation finale : {risk.score} sur 100, dont {risk.model_points:.0f} points venant du modèle et "
        f"{risk.signal_points} points venant des signaux. Ce score classe le niveau d'inquiétude, ce n'est pas une "
        f"probabilité de fraude.")
    return sentences
