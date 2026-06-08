"""Calcul du feu selon l'intention (éviter / concevoir)."""

from app.engines.base import Feu, Phase


def calculer_feu(
  phase: Phase,
  intention: str,
  *,
  infertilite_confirmee: bool = False,
  preovulatoire_infertile: bool = False,
  en_doute: bool = False,
  fenetre_conception: bool = False,
) -> Feu:
  if intention == "concevoir":
    if fenetre_conception or phase == Phase.FERTILE:
      return Feu.VERT
    return Feu.ORANGE

  # Mode éviter
  if en_doute or phase == Phase.INDETERMINEE:
    return Feu.ORANGE
  if phase == Phase.FERTILE:
    return Feu.ROUGE
  if infertilite_confirmee and phase == Phase.POSTOVULATOIRE:
    return Feu.VERT
  if preovulatoire_infertile and phase == Phase.PREOVULATOIRE:
    return Feu.VERT
  return Feu.ORANGE
