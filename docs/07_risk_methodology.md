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
| Phone number | Weak | any phone number |
| Email address | Weak | an address to write to, common in advance-fee fraud |
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

**Results.** `python -m hatari.analysis.signal_check` gives the share of training messages that trigger each signal.

| Signal | English legitimate | English suspicious | French legitimate | French suspicious |
|---|---:|---:|---:|---:|
| Request for money or fees | 0.2% | 6.3% | 0% | 14.3% |
| Request for a code, PIN or password | 0% | 0.2% | 0% | 2.9% |
| Threat on an account | 0% | 0.5% | 0% | 5.7% |
| Shortened or disguised link | 0% | 0.7% | 0% | 0% |
| Money transferred by mistake | 0% | 0.1% | 0% | 0% |
| Promise of a prize or gain | 0.1% | 18.9% | 0% | 7.1% |
| Artificial urgency | 1.2% | 11.8% | 2.1% | 27.1% |
| Mobile Money context | 0% | 0% | 0% | 0% |
| Job offer | 0.2% | 0% | 0% | 0% |
| Investment promise | 0% | 0.2% | 0% | 7.1% |
| Presents itself as an institution | 0.2% | 6.0% | 0% | 0% |
| Link | 0.3% | 19.4% | 0% | 0% |
| Email address | 0% | 1.8% | 0% | 0% |
| Phone number | 0.2% | 58.4% | 0% | 0% |
| Amount of money | 0.3% | 29.7% | 0% | 0% |

- No signal fires on more than 1.2% of the legitimate English messages, so none needed revision.
- **Revision of 22 November 2026.** A bare number of three digits or more counted as a sum of money, so that "Envoyez votre code au 0707070707" was read as a request for money. A bare number now counts only when it has three to six digits. The rate on English suspicious messages fell from 7.9% to 6.3%, the other rates are unchanged.
- Most signals fire on a small share of the suspicious messages. The English suspicious messages are mostly premium-rate spam, which rarely asks for money or codes directly. The signals are designed for the fraud of the target users, which these data barely contain.
- The Mobile Money signal never fires on the training data. Its patterns can only be checked on hand-written examples, which are tests, not evidence.

## 7.7 Known limitations of the method

- The weights and thresholds are design choices. With no real French or West African data, they cannot be calibrated against observed fraud.
- An advance-fee message that promises a large sum and gives an email address, without an explicit request for money, scores low. The test message of `docs/06_evaluation_and_error_analysis.md`, "I have 7.3milion Dollar to transfer to you… Contact …@gmail.com", obtains 23 out of 100 with the category "prize or lottery scam". The weights are not changed to fix this case, because it comes from the test set and a change would tune the method on it.
- The example of the project brief, "Félicitations ! Vous venez de gagner 250 000 FCFA… envoyez immédiatement 2 000 FCFA de frais…", obtains 95 out of 100 and a high risk, not a critical one, because it contains only one strong signal. The method was not adjusted to reproduce the example.
- The language guess relies on frequent function words and can fail on very short or mixed messages.
