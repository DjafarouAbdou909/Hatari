# 1. Problem statement and scope

## 1.1 Problem

People receive fraudulent messages by SMS, WhatsApp and email: fake Mobile Money transfers, prize and lottery announcements, phishing links, fake job offers, impersonation of companies or support services, requests for money, PINs or verification codes, and investment promises. These messages rely on urgency and psychological pressure, and users must decide in real time whether to trust them. Awareness campaigns help, but they do not assist the user at the moment of decision.

## 1.2 Objective

HATARI gives a user a second opinion on one message. The user pastes the text, and HATARI returns:

1. a risk level (low, moderate, high, critical) and a score from 0 to 100;
2. the suspected fraud category, or "unclassified" when evidence is insufficient;
3. the signals observed in the text;
4. an explanation that separates observed signals, the machine learning result and the final assessment;
5. recommended actions.

## 1.3 Users

The primary users are French-speaking mobile users in West Africa, in particular in Côte d'Ivoire, who are not familiar with cybersecurity. The interface is in French. The documentation is in English.

## 1.4 Scope of the MVP

In scope:

- analysis of the text of a single message, pasted by the user;
- a text classifier trained and evaluated on documented public datasets;
- rule-based extraction of fraud signals;
- a documented risk scoring method;
- a local prediction service and a demonstration interface that run without internet access and without paid APIs.

Out of scope:

- checking links, phone numbers or senders against external databases;
- opening or visiting URLs found in messages;
- analysis of images, voice notes or attachments;
- storing user messages or building user accounts;
- any claim about the identity, intention or authenticity of a sender.

## 1.5 Success criteria

- A user can submit a message and receive an assessment that is understandable without technical knowledge.
- The classifier is selected and evaluated on held-out data with precision, recall, F1-score, accuracy and a confusion matrix, and the reported numbers are reproducible from the repository.
- Every signal shown to the user can be traced to the message text or to the model output.
- The limitations, especially the language and regional coverage of the training data, are stated in the documentation and in the interface.

## 1.6 Known risks before any data work

- Public datasets are mostly English SMS spam, which differs from French Mobile Money fraud in Côte d'Ivoire. The model may transfer poorly. This must be measured, not assumed.
- Spam is not the same as fraud. A promotional message can be unwanted without being dangerous. Dataset labels must be read carefully.
- A false negative may lead a user to trust a fraudulent message. The interface must never present a low score as proof of safety.
- A false positive may alarm a user about a legitimate message from a bank or operator. The explanation must make the reasons visible so the user can judge them.

## 1.7 Development workflow

The project follows the order below. The interface is built only after the data, the evaluation strategy and the model are validated.

1. Problem definition and scope (this document).
2. Dataset investigation and data audit.
3. Exploratory data analysis.
4. Preprocessing design.
5. Baseline model.
6. Model comparison.
7. Evaluation and error analysis.
8. Final model selection.
9. Signal extraction and risk scoring.
10. Prediction service and API.
11. Interface.
12. Integration, tests and documentation.
13. Demonstration scenarios.
