# 2. Dataset investigation and data audit

All figures in this document are produced by `python -m hatari.data.audit` after `python -m hatari.data.download`. The raw files are not committed. The download script pins each file to its SHA-256 checksum.

## 2.1 Sources investigated

| Source | Content | Language | Origin | Licence | Used |
|---|---|---|---|---|---|
| UCI SMS Spam Collection (Almeida and Hidalgo, 2011, DOI 10.24432/C5CC84) | 5,574 SMS labelled ham or spam | English | Real messages, collected mainly in the United Kingdom and Singapore | CC BY 4.0, per the UCI record | Yes |
| SMS Phishing Dataset for Machine Learning and Pattern Recognition (Mishra and Soni, 2022, DOI 10.17632/f45bkkt8pr.1) | 5,971 SMS labelled ham, spam or smishing | English | Real messages; part converted to text from images found on the internet | CC BY 4.0, per the Mendeley Data page | Yes |
| French spam text dataset, version 1.1.0 (Djochrist, GitHub, 2026) | 10,000 SMS and emails labelled spam or legitimate | French | Synthetic, generated from templates | CC BY 4.0, per the repository | Yes, as synthetic data only |
| Kaggle SMS Spam Collection, French version (Djochrist, GitHub, 2026) | Machine translation of an English SMS spam corpus | French | Translated | Apache 2.0 on the repository, while the source corpus is CC BY 4.0 | No, see 2.4 |

No public dataset of real French fraudulent messages, and none from Côte d'Ivoire or West Africa, was found. This is the main limitation of the project.

## 2.2 Class distribution and quality

| Source | Messages | Suspicious | Share suspicious | Duplicate messages | Distinct texts | Distinct templates | Damaged characters |
|---|---:|---:|---:|---:|---:|---:|---:|
| UCI | 5,574 | 747 | 13.4% | 447 | 5,127 | 5,094 | 0 |
| Mendeley | 5,971 | 1,127 | 18.9% | 147 | 5,824 | 5,701 | 145 |
| French synthetic, as published | 10,000 | 5,000 | 50.0% | 0 | 10,000 | 441 | 0 |

- A duplicate is the same text up to case, spacing and punctuation. A template is a text up to its digits, so that messages that differ only by a phone number, amount or reference share a template.
- No text carries both a legitimate and a suspicious label within one source.
- Damaged characters are Unicode replacement characters, mostly where the Mendeley conversion lost apostrophes or emoji.
- The median message has 61 characters in UCI, 66 in Mendeley and 145 in the French synthetic set, which mixes SMS and emails.

## 2.3 Overlap between UCI and Mendeley

The two English datasets are not independent. 4,943 distinct texts appear in both. 184 are only in UCI and 881 only in Mendeley.

| Mendeley label | UCI ham | UCI spam |
|---|---:|---:|
| ham | 4,367 | 0 |
| spam | 0 | 309 |
| smishing | 0 | 267 |

- The binary labels agree on every shared text.
- Mendeley splits the UCI spam into spam and smishing, but this split is not consistent. 35 texts appear twice in Mendeley, once as spam and once as smishing.

**Consequence.** The two sources are merged and deduplicated before any split, otherwise the same message could be in training and in evaluation. The finer spam and smishing labels are too noisy to train on. The model learns the binary target, and the threat category is derived from explicit rules, which can be explained and checked.

## 2.4 Exclusion of the translated French dataset

- 50 of its 5,585 non-empty lines have no label. Some of them are text left by the translation tool, such as "Voici la traduction complète des messages demandés (seulement la deuxième colonne) :" and Markdown code fences, others are messages broken across lines.
- It has 5,535 labelled lines against 5,574 messages in the source corpus, so it cannot be aligned with UCI row by row.
- Every message is a translation of a UCI message. If UCI is in training, a translated test message is a paraphrase of a training message, which is leakage. Without alignment, this cannot be controlled.
- Its licence differs from that of the corpus it translates.

It is downloaded for transparency, but it is not used.

## 2.5 The French synthetic dataset

- Its 10,000 messages come from 104 template families. Once digits are masked, only 441 distinct texts remain, at most five per family. The effective diversity is therefore closer to a few hundred messages than to ten thousand.
- The published split keeps each family in one split. The audit confirms that no text and no digit template is shared between splits. Training 6,335, validation 1,834, test 1,831.
- Its spam categories are phishing 1,750, scam 1,250, commercial 500, subscription or premium 500, sextortion or blackmail 500, malware or dangerous link 250, other 250.
- The references are French, for example Lyon or Nantes, and not Ivorian. Amounts in FCFA and Mobile Money operators are absent or rare.

**Label leakage from the generator.** Found during the exploratory analysis of the training part.

- Every legitimate message ends with a reference such as `[référence SM-00001]` or `[référence EM-01837]`, and no suspicious message does.
- Every suspicious message contains a fragment such as `Dossier Lyon-1000.`, and no legitimate message does.
- A model could reach a near perfect score by reading these markers alone. They are removed by `hatari.data.cleaning` before any use.
- Once they are removed, the 10,000 messages reduce to 161 distinct texts, 77 legitimate and 84 suspicious. The corpus keeps one row per distinct text, 117 in training and 44 in test.
- After cleaning, 30% of the legitimate texts contain digits, such as times, and none of the suspicious texts do. Real fraud usually contains amounts and phone numbers. This set therefore teaches a misleading association, which must be watched in the error analysis.

**Consequence.** The French synthetic data is a small supplement of 161 texts. Scores on its 44 test texts measure how well a model recognises the generator's phrasing, not real French fraud. They are reported separately and are never presented as real-world evidence.

## 2.6 Target and grouping decisions

- **Target.** `suspicious` is True when the source labels the message as spam, smishing or fraud. Spam is not always fraud. A promotional message can be unwanted without being dangerous. The interface therefore speaks of risk, and the rule-based signals explain what kind of risk.
- **Grouping.** Splits are made by digit template, so that two messages that differ only by a number never fall on both sides.
- **Separate evaluation.** English real data and French synthetic data are evaluated separately. Pooled scores would hide the language gap.

## 2.7 Limitations

- No real French messages, no West African messages and no Mobile Money fraud in the real data.
- The English real data dates mostly from before 2012, and part of it is premium-rate spam that is rare today.
- About 13% to 19% of the real messages are suspicious. This is the prevalence of these collections, not that of the messages a HATARI user will paste, which are already suspected.
