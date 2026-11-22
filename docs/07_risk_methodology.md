# 7. Signals, threat categories and risk score

This document fixes the method before it is implemented. The weights below are design choices, not learned values. They are checked against the training data in section 7.6, and any change after that check is recorded here.

## 7.1 Why rules in addition to the model

The error analysis of `docs/06_evaluation_and_error_analysis.md` shows that the classifier misses fraud that is obvious to a human, such as an advance-fee message, and raises false alarms on formal French. Rules add three things the model cannot give:

- **traceability**, each signal points to the words that triggered it;
- **knowledge of local fraud**, such as Mobile Money and FCFA amounts, which is absent from the training data;
- **categories**, which the data cannot teach because its spam and smishing labels are unreliable.

## 7.2 Signals

A signal is a pattern observed in the text. Each signal has a strength and returns the matched excerpts as evidence. Patterns cover French and English.

| Signal | Strength | Examples of triggers |
|---|---|---|
| Request for money or fees | Strong | envoyez, payez, frais de, send, pay a fee, deposit |
| Request for a code, PIN or password | Strong | code secret, PIN, mot de passe, OTP, password |
| Threat on an account | Strong | compte suspendu, bloqué, account suspended, verify your account |
| Shortened or disguised link | Strong | bit.ly, tinyurl, a link to an IP address |
| Money transferred by mistake | Strong | envoyé par erreur, renvoyez, sent by mistake |
| Promise of a prize or gain | Medium | félicitations, vous avez gagné, winner, prize, selected |
| Artificial urgency | Medium | urgent, immédiatement, dans les 24 h, expire, now |
| Mobile Money context | Medium | Orange Money, MTN MoMo, Moov Money, Wave, mobile money |
| Job offer | Medium | recrutement, emploi, salaire, job offer |
| Investment promise | Medium | investissement, rendement garanti, doublez, crypto, profit |
| Presents itself as an institution | Medium | service client, banque, customer care, a known operator |
| Link | Weak | any web address |
| Phone number to contact | Weak | a number with call, appelez, contactez |
| Amount of money | Weak | 2 000 FCFA, £100 |

## 7.3 Threat categories

A category is assigned only when its required signals are present. Otherwise the message is unclassified. When several categories apply, they are all listed, the first being the highest in this table.

| Category | Required signals |
|---|---|
| Credential theft | Request for a code, PIN or password |
| Mobile Money scam | Mobile Money context, with a money request, a credential request or money transferred by mistake |
| Advance-fee fraud | Promise of a prize or gain, with a money request |
| Phishing | Threat on an account, with a link or a credential request |
| Fake recruitment | Job offer, with a money request |
| Suspicious investment | Investment promise |
| Impersonation | Presents itself as an institution, with a money request, a credential request or a threat on an account |
| Prize or lottery scam | Promise of a prize or gain, without a money request |
| Malicious or suspicious link | Shortened or disguised link |
| Social engineering | Artificial urgency with any request |

## 7.4 Risk score

The score from 0 to 100 adds two parts.

- **Model part, at most 50 points.** 50 times the calibrated model score.
- **Signal part, at most 50 points.** 20 points per strong signal, 10 per medium signal and 5 per weak signal, capped at 50.

The score is a ranking of concern, not a probability. It is never presented as the probability that a message is fraudulent.

## 7.5 Risk levels

| Level | Condition |
|---|---|
| Critical | Score of at least 75 and at least two strong signals |
| High | Score of at least 50, or a critical score without two strong signals |
| Moderate | Score of at least 25 |
| Low | Score below 25 |

- A low level means that no significant sign was found. It never means that the message is safe, and the interface says so.
- The reliability warning of the interface is shown when the message is shorter than 40 characters or is not detected as English, since the model was trained almost only on English.

## 7.6 Checks before use

Before the interface uses the score, the signals are measured on the training part of the corpus. For each signal, the share of suspicious and legitimate messages that trigger it is reported. A signal that fires on more than 5% of legitimate English messages is revised or downgraded, and the revision is recorded in this document. The test set is not used for this check.
