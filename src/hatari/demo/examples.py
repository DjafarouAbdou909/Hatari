"""Demonstration messages, written for the presentation.

These messages are synthetic. They were written by the project to illustrate
typical cases and are not real messages or evidence of performance. The
interface analyses them with the real model and rules, exactly like any
pasted message. No result is stored for them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    title: str
    kind: str
    text: str


EXAMPLES = (
    Example("Gain contre frais", "Fraude évidente",
            "Félicitations ! Vous venez de gagner 250 000 FCFA. Pour recevoir votre argent, envoyez immédiatement "
            "2 000 FCFA de frais au numéro indiqué. Offre valable pendant 10 minutes."),
    Example("Faux service client", "Fraude moins évidente",
            "Bonjour, ici le service client. Suite à une mise à jour de votre compte Orange Money, merci de nous "
            "communiquer le code que vous allez recevoir par SMS afin d'éviter la suspension de votre ligne."),
    Example("Transfert par erreur", "Fraude moins évidente",
            "Bonsoir maman, j'ai envoyé 25 000 FCFA sur ton numéro par erreur. Stp renvoie-moi ça sur Wave, c'est "
            "pour l'hôpital de mon petit."),
    Example("Colis en attente", "Fraude évidente, en anglais",
            "Your parcel is on hold. Pay the 2.99 GBP delivery fee within 24 hours at http://bit.ly/parcel-fee "
            "or it will be returned."),
    Example("Rendez-vous", "Message légitime",
            "Salut, la réunion de demain est déplacée à 15 h. Je t'envoie l'adresse ce soir. Bonne soirée !"),
    Example("Notification de dépôt", "Message ambigu",
            "Vous avez reçu 15 000 FCFA de KOUASSI A. Nouveau solde : 42 500 FCFA. Merci d'utiliser nos services."),
    Example("Rappel de facture", "Message ambigu",
            "Rappel : votre facture de 18 500 FCFA arrive à échéance le 30. Payez sur l'application officielle ou "
            "en agence."),
)
