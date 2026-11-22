# 9. Model card and deployment

| Item | Value |
|---|---|
| System | HATARI 0.1.0, analysis of suspicious text messages |
| Model | SVM_mask_C1, linear SVM on word unigrams and bigrams after entity masking, Platt calibration |
| Artefact | `models/hatari_model.joblib`, rebuilt by `python -m hatari.models.train`, described by `models/hatari_model.json` |
| Code | `src/hatari/`, `app/streamlit_app.py` |
| Interfaces | Streamlit page in French, FastAPI endpoint `POST /analyze` |

## 9.1 Intended use

- A second opinion on one message, for a person who already doubts it, with the reasons shown.
- Teaching and demonstration of how fraud signals and a text classifier can be combined transparently.

## 9.2 Uses out of scope

- Automatic blocking or filtering of messages without a human decision.
- Any judgement on a person, a sender or an organisation.
- Proof that a message is safe. A low risk only means that no significant sign was found.
- Languages other than English and French, and media other than text.

## 9.3 Training data

Real English SMS from the UCI SMS Spam Collection and the Mendeley SMS Phishing Dataset, merged and deduplicated, and 161 synthetic French texts from the Djochrist dataset after removal of label-revealing markers. Details are in `docs/02_data_audit.md`.

## 9.4 Performance

| Evaluation | Messages | Precision | Recall | F1 and 95% interval |
|---|---:|---:|---:|---|
| Cross-validation, English real | 4,812 | 0.973 | 0.958 | 0.966, 0.956 to 0.974 |
| Single test evaluation, English real | 1,196 | 0.995 | 0.957 | 0.976, 0.959 to 0.989 |
| Cross-validation, French synthetic | 117 | 0.680 | 1.000 | 0.809 |
| Single test evaluation, French synthetic | 44 | 0.933 | 1.000 | 0.966, 0.880 to 1.000 |

The French figures come from synthetic texts of few template families and are not evidence of performance on real French messages.

## 9.5 Known failure modes

- Legitimate formal French, such as operator notifications and bills, is often scored as suspicious by the model.
- Advance-fee fraud without an explicit request for money can score low.
- Very short messages give the model little to work with.
- Disguised words, such as look-alike letters, are studied in `docs/research_obfuscation.md`.

## 9.6 Privacy and security

- Messages are analysed in memory. They are not stored, not logged and not sent to any external service.
- Links in messages are never opened. Evidence excerpts are escaped before display.
- Input is limited to 5,000 characters and validated before analysis.
- Streamlit is configured with a local address, so that it makes no external request at start-up.

## 9.7 Reproducibility

- `requirements-lock.txt` fixes every dependency. The pipeline of the README rebuilds data, model and reports from public sources verified by SHA-256.
- The tests run on every push through `.github/workflows/tests.yml`.

## 9.8 Maintenance

- Retraining with new data requires a new selection protocol and a new held-out set. The current test set has already been used.
- Any change of the signals is checked with `python -m hatari.analysis.signal_check` and recorded in `docs/07_risk_methodology.md`.
