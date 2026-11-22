# HATARI

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5.2-F7931E)
![F1 English test](https://img.shields.io/badge/F1%20English%20test-0.976-success)

**Think before you trust.**

HATARI (Swahili for *danger*) analyses a suspicious text message and explains why it may be fraudulent. A user pastes a message and receives a risk level, a score from 0 to 100, the suspected fraud category, the signals found in the text with the exact words that triggered them, the opinion of a machine learning model and recommended actions. The interface is in French.

HATARI is an academic project. It is a decision aid. It does not verify senders, links or phone numbers, and a low risk never means that a message is safe.

## What it does

| Part | How it works |
|---|---|
| Model | Linear SVM on word unigrams and bigrams, after links, phone numbers, amounts and email addresses are replaced by placeholder tokens, with a Platt-calibrated score |
| Signals | Explicit French and English rules: requests for money or codes, threats on an account, shortened links, transfers "by mistake", promises of gain, urgency, Mobile Money, job and investment offers, institutions, links, numbers, amounts |
| Categories | Credential theft, Mobile Money scam, advance-fee fraud, phishing, fake recruitment, investment scam, impersonation, prize scam, suspicious link, social engineering, or unclassified when evidence is insufficient |
| Risk score | Up to 50 points from the model and up to 50 from the signals. Levels low, moderate, high and critical. It ranks concern and is not a probability |

## Results

The model was selected by grouped cross-validation among 26 configurations, under a rule committed before training, then evaluated once on held-out data.

| Test set | Messages | Precision | Recall | F1, with 95% interval | False positives | Missed |
|---|---:|---:|---:|---|---:|---:|
| Real English SMS | 1,196 | 0.995 | 0.957 | 0.976, 0.959 to 0.989 | 1 | 9 of 209 |
| Synthetic French texts | 44 | 0.933 | 1.000 | 0.966, 0.880 to 1.000 | 1 | 0 of 14 |

The French figures are not evidence. Those texts are synthetic and come from very few template families. In cross-validation, the model flagged 33 of 47 legitimate French texts as suspicious. See the limitations below.

In cross-validation, a character n-gram SVM was significantly better than the selected model, by 0.0096 of F1. The selection rule, fixed before training, treated this gap as equivalent. The selected model was kept to avoid a choice informed by the test, and the comparison is left to a next version (`docs/05_model_comparison.md`, section 5.6).

## Limitations

- **No real French or West African data.** The real training data are English SMS collected mostly before 2012. The French data are 161 synthetic texts that remained after removing label-revealing generator markers from 10,000 messages.
- **False alarms on formal French.** Legitimate operator notifications or bank reminders written in formal French are often scored as suspicious by the model. The interface warns about it and shows the reasons.
- **Fraud without an explicit request.** An advance-fee message that only promises a large sum and gives an email address can score low.
- **Weights set by design.** The weights of the risk score are documented design choices that could not be calibrated on real local fraud.
- **Text only.** No checking of senders, links or numbers against external databases, and no images or voice notes.

The first improvement would be a consented and anonymised collection of real French messages, legitimate ones in particular.

## Installation

Python 3.12. The pinned versions also install on Python 3.11 and 3.13, not on later versions.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[api,app,dev]"
```

For the exact versions used to produce the reported results: `.venv/bin/pip install -r requirements-lock.txt` then `.venv/bin/pip install --no-deps -e .`

## Reproduce the pipeline

```bash
.venv/bin/python -m hatari.data.download        # public datasets, checksum-verified, into data/raw
.venv/bin/python -m hatari.data.audit           # data audit statistics
.venv/bin/python -m hatari.data.corpus          # deduplicated corpus and leakage-free split
.venv/bin/python -m hatari.analysis.eda         # exploratory analysis of the training split
.venv/bin/python -m hatari.models.selection     # cross-validation of the candidates, about 6 minutes
.venv/bin/python -m hatari.models.train         # final model, into models/
.venv/bin/python -m hatari.models.evaluate      # single test evaluation, into reports/
.venv/bin/python -m hatari.models.intervals     # confidence intervals of the reported scores
.venv/bin/python -m hatari.analysis.signal_check
.venv/bin/python -m hatari.research.obfuscation # preregistered robustness study, about 15 minutes
.venv/bin/python -m hatari.models.export        # copy of the model used by the hosted interface
.venv/bin/python -m pytest
```

The raw data and the model of `models/` are not versioned, and the commands above rebuild them. Only the copy used by the hosted interface is versioned, in `app/ressources`.

## Run

```bash
.venv/bin/streamlit run app/streamlit_app.py           # interface, http://localhost:8501
.venv/bin/uvicorn hatari.api.app:app --port 8000       # API, POST /analyze, GET /health
```

Both work without internet access once the model is trained. Messages are analysed in memory and are not stored or logged.

## Deployment

The interface is prepared for Streamlit Community Cloud, from this repository, with `app/streamlit_app.py` as entry point, Python 3.12 and the dependencies of `app/requirements.txt`, placed next to the entry point so that the host reads it before `pyproject.toml`. The hosted version uses the model versioned in `app/ressources`, refreshed after any retraining by `python -m hatari.models.export`. Details are in `docs/09_model_card.md`.

## Repository

```
app/                    Streamlit interface
app/ressources/         model used by the hosted interface
docs/                   documentation, in the order of the work
notebooks/              executed notebooks, one per phase
reports/                cross-validation and test results
src/hatari/data/        download, loading, cleaning, audit, corpus
src/hatari/text/        normalisation, entity masking, input validation
src/hatari/models/      candidates, selection, training, evaluation
src/hatari/analysis/    exploratory analysis, signals, risk
src/hatari/service/     prediction service
src/hatari/api/         FastAPI application
src/hatari/research/    preregistered studies
src/hatari/demo/        synthetic demonstration messages
tests/                  unit and integration tests
```

## Documentation

1. [Problem statement and scope](docs/01_problem_statement.md)
2. [Dataset investigation and data audit](docs/02_data_audit.md)
3. [Exploratory analysis](docs/03_exploratory_analysis.md)
4. [Modelling protocol](docs/04_modelling_protocol.md)
5. [Model comparison](docs/05_model_comparison.md)
6. [Final model, test evaluation and error analysis](docs/06_evaluation_and_error_analysis.md)
7. [Signals, threat categories and risk score](docs/07_risk_methodology.md)
8. [Demonstration scenario](docs/08_demonstration.md)
9. [Model card and deployment](docs/09_model_card.md)

Research studies, each preregistered before any computation:

- [Robustness to obfuscated messages](docs/research_obfuscation.md), with [results](docs/research_obfuscation_results.md): the model resists most disguises but loses 7 points of recall to invisible characters, the rules lose up to 21 points, and a normalisation defence, now adopted, restores both.

## Notebooks

Each notebook runs the tests of its phase and reproduces the figures of the matching document. They are executed and committed with their outputs.

| Notebook | Document |
|---|---|
| [01_data_audit](notebooks/01_data_audit.ipynb) | `docs/02_data_audit.md` |
| [02_exploratory_analysis](notebooks/02_exploratory_analysis.ipynb) | `docs/03_exploratory_analysis.md` |
| [03_model_selection](notebooks/03_model_selection.ipynb) | `docs/05_model_comparison.md` |
| [04_test_evaluation](notebooks/04_test_evaluation.ipynb) | `docs/06_evaluation_and_error_analysis.md` |
| [05_signals_and_risk](notebooks/05_signals_and_risk.ipynb) | `docs/07_risk_methodology.md` |
| [06_study_obfuscation](notebooks/06_study_obfuscation.ipynb) | `docs/research_obfuscation_results.md` |

To run them: `.venv/bin/pip install -e ".[notebooks]"`, then `.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb`.

## Data sources and licences

- Almeida, T. and Hidalgo, J. (2011). SMS Spam Collection. UCI Machine Learning Repository. DOI 10.24432/C5CC84. CC BY 4.0.
- Mishra, S. and Soni, D. (2022). SMS Phishing Dataset for Machine Learning and Pattern Recognition. Mendeley Data. DOI 10.17632/f45bkkt8pr.1. CC BY 4.0.
- Djochrist (2026). French spam text dataset, version 1.1.0, synthetic. GitHub. CC BY 4.0.
