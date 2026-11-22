# 4. Modelling protocol

This protocol was written and committed before any model was trained. It fixes the candidates, the validation scheme and the selection rule, so that the choice of the final model does not depend on the test set or on a favourable reading of the results.

## 4.1 Data

- Training: the training part of the corpus, 4,812 English real messages and 117 French synthetic texts.
- Test: 1,196 English real messages and 44 French synthetic texts. The test set is used once, for the selected model only, after the selection is committed.

## 4.2 Validation

- Five-fold cross-validation on the training part, with `StratifiedGroupKFold`, groups being the digit templates for English and the template families for French, shuffled with a fixed seed.
- Out-of-fold predictions are scored separately on English real messages and on French synthetic texts. Pooled scores are not used for selection, because English dominates training by a factor of forty.

## 4.3 Candidates

| Code | Features | Classifier |
|---|---|---|
| NB | Word TF-IDF, unigrams and bigrams | Multinomial Naive Bayes, the baseline |
| LR | Word TF-IDF, unigrams and bigrams | Logistic regression, balanced class weights |
| SVM | Word TF-IDF, unigrams and bigrams | Linear SVM, balanced class weights |
| LR-char | Word TF-IDF plus character TF-IDF, 2 to 5 characters within word boundaries | Logistic regression, balanced class weights |
| SVM-char | Same features as LR-char | Linear SVM, balanced class weights |

Each candidate is tested with two preprocessings, `normalize` alone and `normalize` with `mask_entities`, as defined in `src/hatari/text/preprocessing.py`. Text is lower-cased by the vectoriser. Hyperparameters keep scikit-learn defaults, except the regularisation strength C of LR and SVM, chosen from 0.1, 1 and 10 by the same cross-validation.

## 4.4 Metrics

For the suspicious class: precision, recall, F1-score. For all messages: accuracy and the confusion matrix. Average precision is also reported, because it does not depend on a threshold. A suspicious message is predicted when the classifier's decision exceeds its default threshold, 0.5 for probabilities and 0 for SVM margins.

## 4.5 Selection rule

1. The selected candidate has the highest F1-score on English real out-of-fold predictions.
2. Candidates within 0.01 of the best F1 are considered equivalent. Among them, the one with the highest recall is preferred, because a missed fraud is more harmful than a false alarm for a tool that the user consults about a message already doubted.
3. If recall is also within 0.01, the simpler candidate is preferred, in the order NB, LR, SVM, LR-char, SVM-char, and normalise alone before masking.
4. A candidate whose French synthetic F1 is below that of NB is reported as such, but the rule is not changed, because the French data is too small and synthetic to drive selection.

The model must also produce a score that can be interpreted on a 0 to 100 scale. If the selected classifier is an SVM, its margin is calibrated by Platt scaling within the training cross-validation, and the calibration is documented.

## 4.6 Threshold

The threshold of the product is not tuned on the test set. If a threshold other than the default is used, it is chosen on out-of-fold predictions of the training part and committed before the test evaluation.
