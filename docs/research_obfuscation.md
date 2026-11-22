# Preregistered study: robustness to obfuscated messages

| Item | Value |
|---|---|
| Project | HATARI |
| Nature | Research study extending the evaluation |
| Status | Plan preregistered, committed before any computation of the study |
| Related documents | `docs/05_model_comparison.md`, `docs/07_risk_methodology.md` |

## 1. Motivation

Fraudsters disguise the words that filters look for. They replace letters by digits, as in "c0de", insert separators, as in "v.e.r.i.f.y", or use letters of other alphabets that look identical, such as the Cyrillic "а" in place of the Latin "a". The evaluation of the project only used messages as collected. This study measures how much the model and the rules lose on disguised fraud, and whether a normalisation defence recovers the loss.

## 2. Research question

How much recall do the selected model, the best character n-gram model and the rules lose when suspicious messages are obfuscated, and does a normalisation that maps look-alike characters, removes invisible characters and joins separated letters recover that recall without harming precision?

## 3. Precautions

- Only the training part of the corpus is used, with the five grouped folds of `docs/04_modelling_protocol.md`. The test set is not read.
- Models are trained on unmodified messages. Obfuscation is applied only to the held-out suspicious messages of each fold, as an attacker would modify only fraud. Legitimate messages are left unchanged, so precision changes only through the defence.
- Every random perturbation uses a fixed seed, 0, and the same perturbed messages are given to every system.
- The analysis is restricted to English real messages, since the French data is synthetic and small.

## 4. Perturbations

| Code | Perturbation | Rate |
|---|---|---|
| P0 | None | |
| P1 | Look-alike letters: a, c, e, i, o, p, x, y replaced by their Cyrillic look-alikes | 30% of eligible letters |
| P2 | Invisible characters: a zero-width space inserted after a letter | 20% of letters |
| P3 | Digit substitution: a 4, e 3, i 1, o 0, s 5 | 30% of eligible letters |
| P4 | Separated letters: dots between the letters of a word of at least four letters | 20% of such words |

## 5. Systems compared

| Code | System |
|---|---|
| M | Selected model, SVM_mask_C1 |
| C | Best character model, SVM-char_normalize_C0.1 |
| R | Rules, a message being flagged when it triggers at least one strong or medium signal |

## 6. Defence

The defence D extends `normalize` before any other step. It applies Unicode NFKC, removes zero-width and other format characters, maps Cyrillic and Greek look-alikes to Latin letters, and joins single letters separated by dots, hyphens or spaces when at least four of them follow each other. It does not reverse digit substitution, which cannot be undone without ambiguity. Each system is evaluated without and with D. With D, the models are retrained on defended training messages, so that training and prediction see the same text.

## 7. Metrics

- Recall on the English suspicious messages of the held-out folds, for each perturbation, system and defence.
- Precision on all English held-out messages, perturbed suspicious and unchanged legitimate, without and with D.
- Loss of recall, the recall under P0 minus the recall under a perturbation, with a 95% interval by paired bootstrap of the message groups, 2,000 draws, seed 0.

## 8. Hypotheses

- **H1.** Without defence, P1 reduces the recall of M by at least 0.10.
- **H2.** Without defence, C loses significantly less recall than M under P1, P2 and P3, each taken separately.
- **H3.** With D, the recall of M under P1 and under P2 is within 0.02 of its recall under P0 without defence.
- **H4.** D does not reduce the precision of M under P0 by more than 0.005.

A hypothesis is refuted when the result contradicts it. Results are reported whatever their outcome.

**Expectations declared before computation.** Word features break when a single letter of a word changes, so H1 is expected to be confirmed. Character n-grams keep part of each word, so H2 is expected to be confirmed for P1 and P3 but is uncertain for P2. Digit substitution is not reversed by D, so no hypothesis is made for P3 with defence.

## 9. Consequences fixed in advance

If H3 and H4 are confirmed, D becomes part of `normalize`, the model is retrained with the frozen configuration, and the change of the clean test scores is reported in a dated addendum of `docs/06_evaluation_and_error_analysis.md`, without any other modification of the model. Otherwise D is not adopted, and the study only documents the weakness.

## 10. Known limits before the study

- The perturbations are synthetic and chosen by the project. Real attackers combine and vary them.
- The English messages date mostly from before 2012, when such obfuscation was rarer than today.
- The rules, written for French and English fraud, were not designed for the premium-rate spam that dominates the English data, so their recall is low from the start.
