# 5. Model comparison

The figures come from `python -m hatari.models.selection`, which writes every configuration to `reports/cross_validation.csv`. They are out-of-fold predictions of the five-fold grouped cross-validation on the training part, as fixed in `docs/04_modelling_protocol.md`. The test set was not used.

## 5.1 Best configuration of each family and preprocessing

English real messages, 836 suspicious and 3,976 legitimate. FP and FN are false positives and false negatives at the default threshold. The last two columns are the French synthetic texts, 70 suspicious and 47 legitimate.

| Configuration | Precision | Recall | F1 | Average precision | FP | FN | French F1 | French FP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NB_normalize | 0.998 | 0.633 | 0.774 | 0.963 | 1 | 307 | 0.833 | 28 |
| NB_mask | 0.998 | 0.695 | 0.820 | 0.970 | 1 | 255 | 0.833 | 28 |
| LR_normalize_C10 | 0.958 | 0.944 | 0.951 | 0.982 | 35 | 47 | 0.809 | 33 |
| LR_mask_C10 | 0.967 | 0.957 | 0.962 | 0.986 | 27 | 36 | 0.805 | 34 |
| SVM_normalize_C1 | 0.970 | 0.938 | 0.954 | 0.985 | 24 | 52 | 0.809 | 33 |
| SVM_mask_C10 | 0.978 | 0.958 | 0.968 | 0.989 | 18 | 35 | 0.824 | 30 |
| LR-char_normalize_C10 | 0.984 | 0.963 | 0.973 | 0.992 | 13 | 31 | 0.814 | 32 |
| LR-char_mask_C10 | 0.977 | 0.962 | 0.969 | 0.992 | 19 | 32 | 0.814 | 32 |
| SVM-char_normalize_C0.1 | 0.987 | 0.964 | 0.975 | 0.991 | 11 | 30 | 0.800 | 35 |
| SVM-char_mask_C10 | 0.984 | 0.959 | 0.972 | 0.993 | 13 | 34 | 0.833 | 28 |

## 5.2 Findings

- **Naive Bayes** is very precise but misses about a third of the suspicious messages at its default threshold. Its average precision of 0.96 to 0.97 shows that its ranking is good and that its threshold is poorly placed for this imbalanced data.
- **Linear models** with balanced class weights reach an F1 of 0.95 to 0.975. The differences between them are small, between 11 and 35 false positives and between 30 and 52 false negatives out of 4,812 messages.
- **Entity masking** helps word models. It lowers the false negatives of LR from 47 to 36 and of SVM from 52 to 35. With character n-grams, which already capture digits and symbols, it no longer helps.
- **Character n-grams** reduce false positives, for example from 18 to 11 for SVM.

## 5.3 Selection

The rule of the protocol is applied mechanically by `hatari.models.selection.select`.

1. The best English F1 is 0.975. Twelve configurations are within 0.01 of it.
2. Among them, the best recall is 0.964, and all twelve are within 0.01 of it.
3. The simplest of the twelve, in the order of the protocol, is **SVM_mask_C1**, a linear SVM on word unigrams and bigrams after entity masking, with C equal to 1. When two configurations differ only by C, the code ranks the smaller C, which is the stronger regularisation, as simpler. The protocol did not state this detail explicitly.

| SVM_mask_C1 | Precision | Recall | F1 | Accuracy | Average precision | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| English real | 0.973 | 0.958 | 0.966 | 0.988 | 0.988 | 3,954 | 22 | 35 | 801 |
| French synthetic | 0.680 | 1.000 | 0.809 | 0.718 | 0.970 | 14 | 33 | 0 | 70 |

**Trade-off accepted by the rule.** The most accurate configuration, SVM-char_normalize_C0.1, produces 11 false positives instead of 22 for the same recall. The rule treats this difference of 0.009 in F1 as equivalent and prefers the simpler model, whose word features are also easier to explain to the user. This choice is kept because it was fixed before the results were seen.

## 5.4 French messages

Two additional diagnostics were run on the same folds for the selected configuration.

- **No transfer from English.** Trained on English messages only, the model detects 7 of the 70 French suspicious texts. The French synthetic data is therefore indispensable, even though it is small.
- **False alarms on unseen legitimate families.** With French data in training, every French suspicious text is detected, but 33 of the 47 legitimate texts are flagged. The highest scores go to a legitimate email, "Réservation confirmée… votre réservation est bien enregistrée", whose template family is absent from the training folds. The French training data has only 21 legitimate templates. The model therefore associates formal French with fraud.
- The average precision of 0.97 shows that the French suspicious texts still rank above the legitimate ones. The problem lies in the threshold and in the lack of legitimate French examples, not in the ranking alone.

**Consequence for the product.** A legitimate formal message in French, for example from a bank or an operator, is likely to be scored as suspicious. The interface must show the signals behind every score so that the user can judge them, and this limitation must be stated. Collecting real, consented and anonymised French messages, legitimate ones in particular, is the first improvement to make.

## 5.5 Next steps

1. Fit SVM_mask_C1 on the whole training part, with Platt calibration of its margin on the grouped folds, as required by the protocol.
2. Evaluate it once on the test set.
3. Analyse its errors.

## 5.6 Confidence intervals, added on 22 November 2026

`python -m hatari.models.intervals` recomputes the out-of-fold predictions of four configurations on the same folds and gives 95% intervals by bootstrap of the message groups, 2,000 draws, seed 0. Results are in `reports/cv_intervals.csv`. English real messages, 4,812 messages in 4,700 groups.

| Configuration | F1 | Interval | F1 minus SVM_mask_C1 | Interval of the difference |
|---|---:|---|---:|---|
| SVM_mask_C1, selected | 0.966 | 0.956 to 0.974 | | |
| SVM-char_normalize_C0.1, best F1 | 0.975 | 0.967 to 0.983 | +0.0096 | +0.0025 to +0.0164 |
| LR_mask_C10 | 0.962 | 0.952 to 0.972 | -0.0035 | -0.0072 to +0.0001 |
| NB_mask | 0.820 | 0.795 to 0.844 | -0.1462 | -0.1696 to -0.1234 |

**Finding.** The character n-gram SVM is significantly better than the selected model, by 0.010 of F1, mostly through fewer false positives. The protocol treated differences below 0.01 as equivalent without a test of significance. This margin was too wide for these data.

**Decision.** The selected model is kept. The selection was frozen before the test evaluation, and changing it now would be informed by the test results. A next version should compare the two configurations on new data, such as the independent French evaluation set planned for the next study, under a protocol that requires a paired interval rather than a fixed margin.
