# 3. Exploratory analysis

Figures come from `python -m hatari.analysis.eda`, which reads only the training part of the corpus built by `python -m hatari.data.corpus`. The test set was not inspected.

## 3.1 Training data

| Language | Origin | Legitimate | Suspicious |
|---|---|---:|---:|
| English | Real | 3,976 | 836 |
| French | Synthetic, cleaned and deduplicated | 47 | 70 |

The English real data dominates training by a factor of about forty.

## 3.2 Message shape

| Language | Class | Median characters | Median words | Median share of upper case letters |
|---|---|---:|---:|---:|
| English | Legitimate | 53 | 11 | 4.5% |
| English | Suspicious | 145 | 24 | 14.4% |
| French | Legitimate | 110 | 17 | 4.6% |
| French | Suspicious | 150.5 | 22 | 2.6% |

Suspicious English messages are longer and use more capitals. The French synthetic messages do not show the capital pattern.

## 3.3 Simple indicators

Share of messages matching an exploratory pattern. These patterns are not the signals of the product, which are designed later.

| Language | Class | Link | Phone number | Money | Any digit | Free or win | Urgency | Code or password |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| English | Legitimate | 0.3% | 0.1% | 0.6% | 16.2% | 2.0% | 9.0% | 0.2% |
| English | Suspicious | 20.6% | 61.6% | 33.1% | 94.0% | 34.8% | 32.5% | 4.1% |
| French | Legitimate | 0% | 0% | 0% | 74.5% | 0% | 2.1% | 0% |
| French | Suspicious | 0% | 0% | 0% | 0% | 0% | 11.4% | 12.9% |

- In the English real data, phone numbers, digits, links and money are strong signs of suspicious messages. Removing digits or links in preprocessing would destroy the strongest signals.
- The French synthetic suspicious texts contain no link, phone number, amount or digit at all. They describe actions in words, such as "ouvrez la page sécurisée" or "contactez le service indiqué". Their legitimate texts contain digits, mostly times. A model trained on them alone would learn that digits mean legitimate, the opposite of real fraud.

## 3.4 Distinctive words

Words with the largest ratio of document frequency between classes. Ties are ordered alphabetically, a correction of 22 November 2026, since the first version of this list depended on the hashing order of Python and changed slightly between runs.

- English suspicious: claim, prize, won, guaranteed, http, awarded, ppm, cs, valid, uk, tone, pobox, winner, ringtone, kyc.
- English legitimate: gt, lt, i'll, he, lor, ü, later, too, she, doing, happy, said, let, morning, lol.
- French suspicious: une, ne, offre, avant, vos, appareil, sur, ouvrez, lien, contactez, alerte, service, recevoir, prévu, payez.
- French legitimate: bientôt, bien, réservation, confirmée, enregistrée, je, merci, h, vers, retour, tu, et, est, à, bonjour.

Observations.

- Many English suspicious words come from British premium-rate spam of the 2000s, such as ringtone, ppm, pobox and tone. They are rare in current Mobile Money fraud.
- The English legitimate words gt and lt are HTML entities. 224 legitimate training messages, and no suspicious one, contain `&lt;`, `&gt;` or `&amp;`, left by the collection of UCI. They are an artefact that reveals the label.
- Words such as lor and ü come from Singaporean SMS. They help to recognise legitimate messages in this corpus, but not in Côte d'Ivoire.
- Personal pronouns and informal words, such as je, tu, i'll and lol, mark legitimate messages in both languages. Fraud often imitates the formal tone of an institution.

## 3.5 Consequences for preprocessing

1. Decode HTML entities, so that `&lt;` becomes `<` and stops revealing the label.
2. Keep digits, links, phone numbers and currency symbols. Replacing a specific number by a placeholder such as a phone or money token may generalise better across countries than the number itself. This is tested empirically in the model comparison, not assumed.
3. Lower-case for word features, but keep a measure of the upper case share available to the rules.
4. Character n-grams are worth testing. They resist spelling tricks such as FL1PKART and share sub-words across English and French, for example "confirm" and "confirmer".
5. Because French data is small and synthetic, the French scores are reported separately, and the transfer from English to realistic French messages must be examined on hand-written, clearly labelled examples.
