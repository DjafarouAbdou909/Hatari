from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
MODEL = Path(__file__).resolve().parents[1] / "models" / "hatari_model.joblib"


@pytest.mark.skipif(not MODEL.exists(), reason="trained model absent, run python -m hatari.models.train")
def test_interface_analyses_an_example_without_error():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    app.sidebar.button[0].click().run()
    analyse = [button for button in app.button if button.label == "Analyser"][0]
    analyse.click().run()
    assert not app.exception
    assert any("Risque" in markdown.value for markdown in app.markdown)


@pytest.mark.skipif(not MODEL.exists(), reason="trained model absent, run python -m hatari.models.train")
def test_interface_rejects_an_empty_message():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP), default_timeout=60).run()
    [button for button in app.button if button.label == "Analyser"][0].click().run()
    assert not app.exception
    assert app.error and "vide" in app.error[0].value
