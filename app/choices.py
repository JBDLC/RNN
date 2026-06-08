"""Libellés et choix pour les formulaires."""

METHODES = [
  ("sensiplan", "Sensiplan (sympto-thermique)"),
  ("billings", "Billings (glaire cervicale seule)"),
  ("cler", "CLER — trois points hauts"),
]

INTENTIONS = [
  ("eviter", "Éviter une grossesse"),
  ("concevoir", "Concevoir"),
]

MODES_DECALAGE = [
  ("exclusion", "Exclusion — exclure les points trop décalés"),
  ("correction", "Correction — ajuster la température (+/- 0,1 °C/h)"),
]

GLAIRE_SENSATIONS = [
  ("", "— Non renseigné —"),
  ("seche", "Sèche"),
  ("humide", "Humide"),
  ("mouillee_glissante", "Mouillée / glissante"),
]

GLAIRE_ASPECTS = [
  ("", "— Non renseigné —"),
  ("rien", "Rien de visible"),
  ("collante_epaisse", "Collante / épaisse"),
  ("cremeuse", "Crémeuse"),
  ("filante_transparente", "Filante / transparente"),
]

SAIGNEMENTS = [
  ("rien", "Aucun"),
  ("leger", "Léger"),
  ("regles", "Règles"),
]

TESTS_LH = [
  ("", "— Non fait —"),
  ("negatif", "Négatif"),
  ("positif", "Positif"),
]

COL_HAUTEURS = [
  ("", "— Non renseigné —"),
  ("bas", "Bas"),
  ("moyen", "Moyen"),
  ("haut", "Haut"),
]

COL_OUVERTURES = [
  ("", "— Non renseigné —"),
  ("ferme", "Fermé"),
  ("entrouvert", "Entrouvert"),
  ("ouvert", "Ouvert"),
]

COL_CONSISTANCES = [
  ("", "— Non renseigné —"),
  ("dur", "Dur"),
  ("mou", "Mou"),
]

MOTIFS_DOUTE = [
  ("fievre", "Fièvre"),
  ("alcool", "Alcool"),
  ("sommeil_court", "Sommeil court / perturbé"),
  ("voyage", "Voyage / décalage horaire"),
  ("prise_decalee", "Prise décalée"),
  ("autre", "Autre"),
]

METHODE_LABELS = dict(METHODES)
INTENTION_LABELS = dict(INTENTIONS)
MOTIF_DOUTE_LABELS = dict(MOTIFS_DOUTE)


def methode_thermique(methode: str) -> bool:
  """True si la méthode utilise la température."""
  return methode in ("sensiplan", "cler")


PHASE_LABELS = {
  "preovulatoire": "Préovulatoire",
  "fertile": "Fertile",
  "postovulatoire": "Post-ovulatoire",
  "indeterminee": "Indéterminée",
}

FEU_LABELS = {
  "vert": "Vert",
  "orange": "Orange",
  "rouge": "Rouge",
}
