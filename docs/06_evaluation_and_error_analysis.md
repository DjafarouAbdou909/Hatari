# 6. Final model, test evaluation and error analysis

## 6.1 Final model

`python -m hatari.models.train` fits SVM_mask_C1, selected in `docs/05_model_comparison.md`, on the 4,929 training messages. Its margin is turned into a score between 0 and 1 by Platt scaling, fitted on the out-of-fold margins of the same five grouped folds as the selection. The final SVM is then refitted on the whole training part. The decision threshold stays at the default of 0.5, as no other threshold was committed before the test. The model file is not versioned. `models/hatari_model.json` records its configuration, the checksum of the corpus it was trained on and its own checksum.

## 6.2 Test results

`python -m hatari.models.evaluate` was run once, after the selection and the final model were committed. Results are in `reports/test_evaluation.csv`.

| Test set | Messages | Precision | Recall | F1 | Accuracy | Average precision | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| English real | 1,196 | 0.995 | 0.957 | 0.976 | 0.992 | 0.995 | 986 | 1 | 9 | 200 |
| French synthetic | 44 | 0.933 | 1.000 | 0.966 | 0.977 | 1.000 | 29 | 1 | 0 | 14 |

- **English.** The test scores are close to the cross-validation scores, F1 0.976 against 0.966. The model misses 9 of 209 suspicious messages and raises 1 false alarm among 987 legitimate ones.
- **French.** These figures must not be read as evidence. The 30 legitimate test texts come from only 4 template families, and the 14 suspicious ones from 14. In cross-validation, on 16 legitimate families, the model flagged 33 of 47 legitimate texts. The cross-validation result is the more informative one, and it shows a serious risk of false alarms on legitimate French messages.

## 6.3 Calibration

On the English test set, the Brier score is 0.008. The score agrees with the observed share of suspicious messages where most messages fall.

| Score | Messages | Mean score | Observed share suspicious |
|---|---:|---:|---:|
| 0 to 0.1 | 982 | 0.007 | 0.006 |
| 0.1 to 0.3 | 10 | 0.159 | 0.300 |
| 0.3 to 0.5 | 3 | 0.372 | 0 |
| 0.5 to 0.7 | 1 | 0.583 | 0 |
| 0.7 to 0.9 | 13 | 0.819 | 1 |
| 0.9 to 1 | 187 | 0.982 | 1 |

The middle bins contain too few messages to judge. The calibration also reflects the prevalence of these collections, about 17% suspicious, and not that of the messages a user pastes into HATARI, which are already doubted. **The model score is therefore not presented to the user as a probability of fraud.**

## 6.4 Error analysis

All 11 errors are listed in `reports/test_errors.csv`.

**Missed suspicious messages, English.**

| Score | Message, shortened | Reading |
|---:|---|---|
| 0.011 | How come it takes so little time for a child who is afraid of the dark to become a teenager… | A joke with no request. Probably a labelling error of the source |
| 0.025 | Swayamvara By David Hair… a story of reincarnation… | Book promotion, harmless |
| 0.065 | LookAtMe!: Thanks for your purchase of a video clip… you've been charged 35p… | Premium-rate subscription |
| 0.088 | Overcome programming challenges for multicore… Attend Intel session… | Event promotion, harmless |
| 0.090 | Filthy stories and GIRLS waiting for your | Adult spam, very short |
| 0.097 | My name is Theresa & I have 7.3milion Dollar to transfer to you for charity work… Contact … @gmail.com | **Advance-fee fraud**, a serious miss |
| 0.110 | Burger King - Wanna play footy at a top stadium?… walk out a winner | Promotion |
| 0.158 | You will be receiving this week's Triple Echo ringtone shortly | Premium-rate subscription |
| 0.209 | Sorry I missed your call let's talk when you have the time. I'm on 07090201529 | Callback scam to a premium number, written like a personal message |

**False alarms.**

| Score | Message | Reading |
|---:|---|---|
| 0.583 | Mathews or tait or edwards or anderson (English) | Short list of names, no context |
| 0.561 | Objet : Question concernant le dossier… pourriez-vous me préciser la prochaine étape… (French) | Formal French, the weakness found in cross-validation |

**What the errors show.**

1. Five of the nine misses are promotions or jokes. The binary target mixes spam and fraud, and these messages carry little risk.
2. Two misses are real fraud patterns that the model cannot recognise from vocabulary alone. The advance-fee message promises a large sum of money and asks the reader to make contact. The callback message imitates a personal message and only reveals itself through a premium-rate number. Explicit rules on money promises, contact requests and premium-rate numbers can catch such patterns, which justifies combining the model with rules.
3. The model is weak on very short messages, which give it few words.
4. Formal French remains the main source of false alarms.

## 6.5 Consequences for the product

- The risk shown to the user combines the model score with observed signals. Each signal is traced to the text, so that the user can judge a false alarm such as a formal French message.
- A low score never means that a message is safe. A message such as the advance-fee one above can obtain a low model score.
- Short messages and French messages call for an explicit warning of lower reliability.

## 6.6 Confidence intervals, added on 22 November 2026

`python -m hatari.models.intervals` applies the saved model to the test set again, reproducing the predictions of section 6.2, and adds 95% intervals by bootstrap of the message groups. Results are in `reports/test_intervals.csv`. No choice is made from them.

| Test set | Groups | Precision | Recall | F1 |
|---|---:|---|---|---|
| English real, 1,196 messages | 1,175 | 0.984 to 1.000 | 0.928 to 0.981 | 0.959 to 0.989 |
| French synthetic, 44 texts | 18 | 0.786 to 1.000 | 1.000 to 1.000 | 0.880 to 1.000 |

The English interval is narrow because the test set is large and its messages are nearly independent. The French interval rests on 18 groups only, and its recall of 1 on 14 groups says little about real French fraud.

## 6.7 Retraining with the obfuscation defence, 22 November 2026

After the study of `docs/research_obfuscation_results.md`, the obfuscation defence was integrated into `normalize`, as its plan required, and the model was retrained with the same frozen configuration. The saved model was then applied once more to the test set.

- The test scores and the list of misclassified messages are identical to those of sections 6.2 and 6.4, to the fourth decimal. No test message contains invisible characters, look-alike letters or four separated letters that the defence would change.
- The intervals of section 6.6 are therefore unchanged.
- The new model file is described by `models/hatari_model.json`.
