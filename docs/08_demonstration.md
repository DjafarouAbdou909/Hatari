# 8. Demonstration scenario

The demonstration lasts about five minutes and runs without internet access. Every result is computed live by the model and the rules. The demonstration messages of `src/hatari/demo/examples.py` were written by the project. They are synthetic and only illustrate typical cases.

## 8.1 Before the presentation

```bash
.venv/bin/python -m hatari.models.train      # if models/hatari_model.joblib is absent
.venv/bin/python -m pytest                   # every test must pass
.venv/bin/streamlit run app/streamlit_app.py
```

Open http://localhost:8501 and check that the sidebar lists the seven examples.

## 8.2 Expected results

Computed on 22 November 2026 with the model of `models/hatari_model.json`. They will change if the model or the rules change.

| Example | Kind | Score | Level | Model score | Categories |
|---|---|---:|---|---:|---|
| Gain contre frais | Obvious fraud | 95 | High | 0.99 | Advance-fee fraud, social engineering |
| Faux service client | Less obvious fraud | 99 | Critical | 0.99 | Credential theft, Mobile Money scam, phishing, impersonation |
| Transfert par erreur | Less obvious fraud | 83 | Critical | 0.65 | Mobile Money scam |
| Colis en attente | Obvious fraud, English | 98 | Critical | 0.95 | Suspicious link, social engineering |
| Rendez-vous | Legitimate | 1 | Low | 0.03 | Unclassified |
| Notification de dépôt | Ambiguous | 54 | High | 0.99 | Unclassified |
| Rappel de facture | Ambiguous | 52 | High | 0.94 | Unclassified |

## 8.3 Scenario

1. **The problem.** Fraudulent SMS and WhatsApp messages exploit urgency and trust, and the user must decide alone and quickly.
2. **The purpose.** HATARI gives a second opinion and, above all, shows why.
3. **A fraudulent message.** Click "Gain contre frais", then "Analyser". Show the high risk, the advance-fee category and the gauge.
4. **The indicators.** Read the evidence under each signal, such as « envoyez immédiatement 2 000 » and « Vous venez de gagner ». Point out that each one is an excerpt of the message.
5. **A legitimate message.** Click "Rendez-vous". The risk is low, and the interface says that this does not guarantee safety.
6. **Comparison.** The model gives 0.99 to the first message and 0.03 to the second. The signals make the difference visible to the user.
7. **Training and evaluation.** Open "Comment fonctionne HATARI". Public English SMS, 26 configurations compared by grouped cross-validation, a rule fixed before training, a single test evaluation with an F1 of 0.976 on real English SMS.
8. **Limitations.** Click "Notification de dépôt". The model scores a plausible legitimate notification as suspicious, while no strong signal is present. This is the bias towards formal French measured in `docs/05_model_comparison.md`, due to the lack of real French messages. It is the first thing to improve.

## 8.4 If something goes wrong

- **"Le modèle n'est pas disponible".** Run `python -m hatari.models.train`, after `python -m hatari.data.download` and `python -m hatari.data.corpus` if the data are absent.
- **Port already in use.** Add `--server.port 8502` to the streamlit command.
