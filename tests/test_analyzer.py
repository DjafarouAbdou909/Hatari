import joblib
import pandas as pd
import pytest

from hatari.models.train import MODEL_FILE, fit
from hatari.service.analyzer import Analyzer, ModelNotFound
from hatari.text.preprocessing import InvalidMessage


@pytest.fixture(scope="module")
def analyzer(tmp_path_factory):
    suspicious = [f"Congratulations you won {i}000 pounds, send the fee now and call 0800{i:06d}" for i in range(15)]
    legitimate = [f"See you at {i} for lunch with the team, I will call you later" for i in range(15)]
    frame = pd.DataFrame({"text": suspicious + legitimate, "suspicious": [True] * 15 + [False] * 15,
                          "language": "en", "group": [f"s{i}" for i in range(15)] + [f"l{i}" for i in range(15)]})
    directory = tmp_path_factory.mktemp("models")
    joblib.dump(fit(frame), directory / MODEL_FILE)
    return Analyzer(directory)


def test_missing_model_gives_an_actionable_error(tmp_path):
    with pytest.raises(ModelNotFound, match="hatari.models.train"):
        Analyzer(tmp_path)


def test_analysis_separates_signals_model_and_final_assessment(analyzer):
    result = analyzer.analyze("Congratulations you won 5000 pounds, send the fee now and call 08001234567")

    assert result.model.label == "suspect"
    assert result.model.suspicious_terms
    assert {"prize_promise", "money_request", "phone_number"} <= {signal.id for signal in result.signals}
    assert result.categories[0]["id"] == "advance_fee"
    assert 0 <= result.risk.score <= 100
    assert result.explanation[0].startswith("Signaux observés")
    assert result.explanation[1].startswith("Modèle")
    assert "pas une probabilité" in result.explanation[2]


def test_legitimate_message_is_low_risk_without_claiming_safety(analyzer):
    result = analyzer.analyze("See you at 12 for lunch with the team, I will call you later")

    assert result.risk.level == "low"
    assert result.categories == [{"id": "unclassified", "label": "Non classé"}]
    assert any("ne garantit pas" in line for line in result.recommendations)


def test_invalid_input_is_rejected(analyzer):
    with pytest.raises(InvalidMessage):
        analyzer.analyze("   ")


def test_analysis_is_serialisable(analyzer):
    data = analyzer.analyze("Call 08001234567 now to claim your prize").to_dict()
    assert set(data) == {"risk", "model", "signals", "categories", "explanation", "recommendations", "warnings"}
