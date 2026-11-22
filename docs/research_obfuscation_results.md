# Results of the study on obfuscated messages

| Item | Value |
|---|---|
| Project | HATARI |
| Preregistered plan | `docs/research_obfuscation.md`, committed before any computation |
| Code | `src/hatari/research/obfuscation.py`, `src/hatari/text/defence.py` and `tests/test_obfuscation.py` |
| Results | `reports/obfuscation_results.csv` and `reports/obfuscation_hypotheses.csv` |
| Status | Study completed, two hypotheses confirmed and two refuted, defence adopted |

## 1. Summary

The selected model resists look-alike letters, digit substitution and separated letters better than expected, but loses 7 points of recall when invisible characters are inserted. The rules are far more fragile and lose up to 21 points. A normalisation defence that removes invisible characters, maps look-alike letters and joins separated letters restores the recall of every system under these attacks, without changing precision on ordinary messages. As fixed in the plan, the defence is adopted.

## 2. Results

English real messages of the five held-out folds, 836 suspicious and 3,976 legitimate. N means without defence, D with defence. The loss is the recall under no perturbation without defence, minus the recall in the cell.

| System | Perturbation | Recall, N | Loss, N, and 95% interval | Recall, D | Loss, D |
|---|---|---:|---|---:|---:|
| Selected model M | P0, none | 0.958 | | 0.958 | 0.000 |
| | P1, look-alike letters | 0.934 | 0.024, 0.012 to 0.036 | 0.958 | 0.000 |
| | P2, invisible characters | 0.886 | 0.072, 0.055 to 0.090 | 0.958 | 0.000 |
| | P3, digit substitution | 0.944 | 0.014, 0.005 to 0.025 | 0.944 | 0.014 |
| | P4, separated letters | 0.955 | 0.004, 0.000 to 0.008 | 0.957 | 0.001 |
| Character model C | P0 | 0.964 | | 0.964 | 0.000 |
| | P1 | 0.941 | 0.023, 0.011 to 0.034 | 0.964 | 0.000 |
| | P2 | 0.945 | 0.019, 0.011 to 0.029 | 0.964 | 0.000 |
| | P3 | 0.958 | 0.006, -0.001 to 0.014 | 0.958 | 0.006 |
| | P4 | 0.957 | 0.007, 0.002 to 0.013 | 0.964 | 0.000 |
| Rules R | P0 | 0.355 | | 0.355 | 0.000 |
| | P1 | 0.185 | 0.170, 0.139 to 0.203 | 0.355 | 0.000 |
| | P2 | 0.148 | 0.207, 0.175 to 0.241 | 0.355 | 0.000 |
| | P3 | 0.202 | 0.153, 0.124 to 0.184 | 0.202 | 0.153 |
| | P4 | 0.313 | 0.042, 0.027 to 0.061 | 0.347 | 0.008 |

- Precision of M stays between 0.971 and 0.973 in every cell, and that of C between 0.986 and 0.987.
- The rules flag a message when it triggers at least one strong or medium signal. Their recall of 0.355 without perturbation reflects English premium-rate spam, for which they were not designed.

## 3. Hypotheses

| Hypothesis | Summary | Verdict | Decisive element |
|---|---|---|---|
| H1 | P1 reduces the recall of M by at least 0.10 | Refuted | Loss of 0.024 |
| H2 | C loses significantly less recall than M under P1, P2 and P3 | Refuted | Significant for P2 only, a gap of 0.053, 0.035 to 0.070. P1 0.001, -0.015 to 0.017. P3 0.008, -0.002 to 0.019 |
| H3 | With D, the recall of M under P1 and P2 is within 0.02 of its clean recall | Confirmed | 0.958 under both, equal to the clean recall |
| H4 | D does not reduce the precision of M on clean messages by more than 0.005 | Confirmed | Change of 0.000 |

**Against the declared expectations.** H1 was expected to be confirmed and is refuted. The masked tokens for numbers, amounts and links, which carry most of the signal of English spam, are not affected by look-alike letters. H2 was expected for P1 and P3 and is confirmed for neither, but character n-grams protect clearly against invisible characters.

## 4. Analysis

- **Invisible characters are the main threat to the model.** A zero-width space splits a word into two unknown tokens, while a look-alike letter changes only one word at a time.
- **The rules are the weak point.** A regular expression fails as soon as one letter of its keyword changes. Without defence, an attacker could erase the evidence shown to the user while the model still detects the message.
- **The defence closes three of the four attacks.** Digit substitution remains, since "c0de" cannot be turned back into "code" without risking errors on real numbers.

## 5. Consequences

As fixed in section 9 of the plan, H3 and H4 being confirmed, the defence is integrated into `normalize` on 22 November 2026. It therefore applies to the model and to the rules, in training and in the interface. The model is retrained with its frozen configuration. The effect on the clean test scores is reported in section 6.7 of `docs/06_evaluation_and_error_analysis.md`.

Evidence excerpts are now taken from the defended text. A word written with look-alike letters is shown in Latin letters.

## 6. Limits

- The perturbations are synthetic, chosen by the project and applied one at a time.
- Digit substitution is not defended, and attackers can combine techniques.
- The study uses English messages from before 2012. Obfuscation is more common in recent fraud.
