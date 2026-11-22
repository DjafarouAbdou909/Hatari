"""HATARI interface.

Run from the repository root:

    streamlit run app/streamlit_app.py

The same file is the entry point of the hosted version. The message is analysed
in the process that serves the page, with the model of app/ressources when it
exists. It is not stored, not logged and not sent to any other service.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hatari.analysis.risk import CRITICAL, HIGH, LOW, MODERATE
from hatari.demo.examples import EXAMPLES
from hatari.service.analyzer import Analyzer, ModelNotFound
from hatari.models.train import MODEL_FILE
from hatari.text.preprocessing import MAX_CHARACTERS, InvalidMessage

RESOURCES = ROOT / "app" / "ressources"
LEVEL_COLORS = {LOW: "#2E9E6B", MODERATE: "#E0A526", HIGH: "#E2692B", CRITICAL: "#D64545"}
STRENGTH_LABELS = {"strong": "fort", "medium": "moyen", "weak": "faible"}

st.set_page_config(page_title="HATARI · Think before you trust", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1100px; padding-top: 2rem;}
    .brand {font-size: 2.6rem; font-weight: 800; letter-spacing: 0.08em; margin-bottom: 0;}
    .brand span {color: #E2692B;}
    .tagline {color: #9FB0C8; margin-top: -0.4rem; font-size: 1.05rem;}
    .card {background: #16263D; border: 1px solid #24395A; border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;}
    .risk {border-left: 8px solid var(--level); }
    .risk-label {font-size: 1.6rem; font-weight: 800; color: var(--level);}
    .risk-score {font-size: 1.1rem; color: #C9D4E5;}
    .chip {display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; margin: 0.15rem 0.3rem 0.15rem 0;
           background: #24395A; color: #E8EDF5; font-size: 0.85rem;}
    .evidence {color: #9FB0C8; font-style: italic;}
    .muted {color: #9FB0C8; font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_analyzer() -> Analyzer:
    if (RESOURCES / MODEL_FILE).exists():
        return Analyzer(RESOURCES)
    return Analyzer()


@st.cache_data
def load_test_metrics() -> pd.DataFrame | None:
    path = ROOT / "reports" / "test_evaluation.csv"
    return pd.read_csv(path) if path.exists() else None


def gauge(score: int, color: str) -> go.Figure:
    figure = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": " / 100", "font": {"size": 30, "color": "#E8EDF5"}},
        gauge={"axis": {"range": [0, 100], "tickcolor": "#9FB0C8"}, "bar": {"color": color},
               "bgcolor": "#0F1B2D",
               "steps": [{"range": [0, 25], "color": "#173A2E"}, {"range": [25, 50], "color": "#3A3317"},
                         {"range": [50, 75], "color": "#3E2717"}, {"range": [75, 100], "color": "#3E1A1A"}]},
    ))
    figure.update_layout(height=210, margin={"l": 35, "r": 45, "t": 20, "b": 0}, paper_bgcolor="rgba(0,0,0,0)",
                         font={"color": "#E8EDF5"})
    return figure


def composition(model_points: float, signal_points: int) -> go.Figure:
    figure = go.Figure()
    figure.add_bar(y=["Score"], x=[model_points], orientation="h", name="Modèle", marker_color="#5B8DEF",
                   hovertemplate="Modèle : %{x:.0f} points<extra></extra>")
    figure.add_bar(y=["Score"], x=[signal_points], orientation="h", name="Signaux", marker_color="#E2692B",
                   hovertemplate="Signaux : %{x} points<extra></extra>")
    figure.update_layout(barmode="stack", height=120, margin={"l": 10, "r": 25, "t": 0, "b": 0},
                         xaxis={"range": [0, 100], "color": "#9FB0C8"}, yaxis={"visible": False},
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         legend={"orientation": "h", "y": -0.6, "traceorder": "normal", "font": {"color": "#E8EDF5"}})
    return figure


def show_result(result) -> None:
    risk = result.risk
    color = LEVEL_COLORS[risk.level]
    categories = "".join(f'<span class="chip">{html.escape(c["label"])}</span>' for c in result.categories)
    left, right = st.columns([3, 2])
    with left:
        st.markdown(
            f'<div class="card risk" style="--level:{color}">'
            f'<div class="risk-label">{html.escape(risk.level_label)}</div>'
            f'<div class="risk-score">Score d\'inquiétude {risk.score} sur 100</div>'
            f'<div style="margin-top:0.5rem">Catégorie : {categories}</div></div>',
            unsafe_allow_html=True,
        )
        for warning in result.warnings:
            st.warning(warning, icon="⚠️")
    with right:
        st.plotly_chart(gauge(risk.score, color), use_container_width=True, config={"displayModeBar": False})
        st.plotly_chart(composition(risk.model_points, risk.signal_points), use_container_width=True,
                        config={"displayModeBar": False})

    observed, model, final = st.columns(3)
    with observed:
        st.markdown("#### Signaux observés")
        st.caption("Ce qui est écrit dans le message, détecté par des règles explicites.")
        if not result.signals:
            st.markdown('<div class="muted">Aucun des signaux recherchés n\'a été trouvé.</div>', unsafe_allow_html=True)
        for signal in result.signals:
            evidence = " · ".join(f"« {html.escape(e)} »" for e in signal.evidence)
            st.markdown(
                f'<div class="card"><b>{html.escape(signal.label)}</b> '
                f'<span class="chip">{STRENGTH_LABELS[signal.strength]}</span><br>'
                f'<span class="evidence">{evidence}</span></div>',
                unsafe_allow_html=True,
            )
    with model:
        st.markdown("#### Avis du modèle")
        st.caption("Classifieur entraîné sur des messages publics étiquetés.")
        st.metric("Score du modèle", f"{result.model.score:.2f}".replace(".", ","), help="Entre 0 et 1. Ce n'est pas une probabilité de fraude.")
        st.markdown(result.model.summary)
        if result.model.suspicious_terms:
            terms = "".join(f'<span class="chip">{html.escape(t)}</span>' for t in result.model.suspicious_terms)
            st.markdown(f"Termes qui ont le plus pesé : {terms}", unsafe_allow_html=True)
    with final:
        st.markdown("#### Évaluation finale")
        st.caption("Combinaison documentée du modèle et des signaux.")
        for sentence in result.explanation[2:]:
            st.markdown(sentence)

    st.markdown("#### Que faire ?")
    for advice in result.recommendations:
        st.markdown(f"- {advice}")


def about() -> None:
    with st.expander("Comment fonctionne HATARI, et ses limites"):
        st.markdown(
            "- **Modèle.** Un SVM linéaire sur les mots du message, après remplacement des liens, numéros, montants "
            "et adresses par des jetons. Il a été choisi par une validation croisée groupée, selon une règle fixée "
            "avant l'entraînement.\n"
            "- **Données.** Des SMS publics réels en anglais, UCI SMS Spam Collection et Mendeley SMS Phishing, et "
            "161 textes français synthétiques. Aucun message réel français ou ivoirien n'était disponible.\n"
            "- **Signaux.** Des règles explicites, en français et en anglais, sur les demandes d'argent ou de codes, "
            "les menaces sur un compte, l'urgence, les liens et le Mobile Money.\n"
            "- **Score.** Jusqu'à 50 points pour le modèle et 50 points pour les signaux. Le score classe le niveau "
            "d'inquiétude. Ce n'est pas une probabilité de fraude.\n"
            "- **Limites.** Le modèle juge souvent suspects des messages français légitimes au ton formel, comme les "
            "notifications d'opérateurs. Un risque faible ne garantit jamais qu'un message est sûr. HATARI ne peut "
            "pas vérifier l'identité de l'expéditeur."
        )
        metrics = load_test_metrics()
        if metrics is not None:
            english = metrics[metrics["language"] == "en"].iloc[0]
            st.markdown(
                f"**Évaluation unique sur des SMS anglais réels tenus à l'écart**, {int(english['messages'])} messages : "
                f"précision {english['precision']:.3f}, rappel {english['recall']:.3f}, F1 {english['f1']:.3f}. "
                "Ces chiffres ne valent pas pour des messages français."
            )


st.markdown('<p class="brand">HATA<span>RI</span></p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Think before you trust. <i>Hatari</i> signifie « danger » en swahili.</p>',
            unsafe_allow_html=True)
st.markdown("Collez un message reçu par SMS, WhatsApp ou e-mail. HATARI repère les signes d'arnaque et explique "
            "pourquoi le message peut être dangereux.")
st.info("🔒 Le message est analysé par le serveur qui affiche cette page, votre ordinateur en local ou l'hébergeur "
        "en ligne. HATARI ne le conserve pas, ne l'écrit dans aucun journal et ne l'envoie à aucun autre service. "
        "Les liens du message ne sont jamais ouverts. Évitez d'y laisser un code secret ou un numéro de compte.")

try:
    analyzer = load_analyzer()
except ModelNotFound as error:
    st.error(f"Le modèle n'est pas disponible. {error}")
    st.stop()

if "message" not in st.session_state:
    st.session_state["message"] = ""

with st.sidebar:
    st.markdown("### Exemples de démonstration")
    st.caption("Messages rédigés pour la démonstration, analysés comme n'importe quel message.")
    for index, example in enumerate(EXAMPLES):
        if st.button(f"{example.title} · {example.kind}", key=f"example_{index}", use_container_width=True):
            st.session_state["message"] = example.text

message = st.text_area("Message à analyser", key="message", height=150, max_chars=MAX_CHARACTERS,
                       placeholder="Collez ici le message suspect…")
if st.button("Analyser", type="primary"):
    try:
        with st.spinner("Analyse du texte en cours…"):
            result = analyzer.analyze(message)
    except InvalidMessage as error:
        st.error(str(error))
    else:
        show_result(result)

about()
st.caption("HATARI est un outil d'aide à la décision. Il ne remplace pas la vigilance ni la vérification auprès "
           "de l'organisme concerné. Projet académique, version 0.1.0.")
