# HATARI

**Think before you trust.**

HATARI (Swahili for *danger*) analyses a suspicious text message and explains why it may be fraudulent. It combines a text classifier trained on public datasets with transparent, rule-based detection of fraud signals such as requests for money, urgency, credential requests and suspicious links.

> Status: early development. Nothing described below as planned is implemented yet.

## Documentation

- [Problem statement and scope](docs/01_problem_statement.md)
- [Dataset investigation and data audit](docs/02_data_audit.md)
- [Exploratory analysis](docs/03_exploratory_analysis.md)
- [Modelling protocol](docs/04_modelling_protocol.md)
- [Model comparison](docs/05_model_comparison.md)

## Principles

- Real model inference only. No hardcoded predictions, no fabricated metrics.
- Messages are analysed locally and are not stored or logged.
- A low score never means that a message is safe.
