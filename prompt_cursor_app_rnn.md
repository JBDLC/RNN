# Prompt pour Cursor — Application de Régulation Naturelle des Naissances (RNN)

> Colle ce prompt dans Cursor. Il décrit l'application à construire de A à Z. Construis l'app de façon incrémentale, en commençant par le squelette et le Moteur Sensiplan, puis Billings, puis CLER. Demande-moi confirmation avant de passer à l'étape suivante.

---

## 1. Contexte et objectif

Je veux une **web app Python / Flask**, hébergeable sur **Render**, qui assiste un couple pratiquant la Régulation Naturelle des Naissances. L'utilisateur saisit ses observations chaque jour ; l'app calcule sa phase de fertilité et indique si une union est possible (selon que le couple cherche à éviter ou à concevoir).

**Trois méthodes** sont proposées au choix, chacune avec son propre **moteur de calcul** (logique métier indépendante) mais une **interface de sortie commune** :
1. **Sensiplan** (sympto-thermique, le plus rigoureux)
2. **Billings** (glaire cervicale seule)
3. **CLER — méthode des trois points hauts** (sympto-thermique francophone, avec visualisation de courbe)

**Avertissement central, non négociable** : cette app n'est PAS un dispositif médical, n'est pas contraceptive en elle-même, et ne remplace pas l'apprentissage auprès d'un moniteur certifié (CLER, Sensiplan, WOOMB/Billings). Les avertissements doivent être visibles et forts (voir §9).

---

## 2. Stack technique

- **Backend** : Python 3.11+, Flask, SQLAlchemy.
- **Base de données** : SQLite en local, PostgreSQL en production (compatible Render). Utiliser `DATABASE_URL` en variable d'environnement.
- **Frontend** : templates Jinja2 + un peu de JS vanilla. Pour la courbe de température, utiliser **Chart.js** (CDN). Pas de framework lourd.
- **Auth** : simple, un couple = un compte. Flask-Login. Mot de passe haché (werkzeug).
- **Déploiement** : prévoir `requirements.txt`, `Procfile` (gunicorn), et gérer le port via `PORT`. Migrations avec Flask-Migrate.
- Code commenté en français, noms de variables clairs.

---

## 3. Architecture des moteurs

Chaque méthode = une classe qui hérite d'une interface commune. Objectif : mutualiser l'affichage, isoler la logique.

```python
from dataclasses import dataclass
from enum import Enum

class Phase(Enum):
    PREOVULATOIRE = "preovulatoire"
    FERTILE = "fertile"
    POSTOVULATOIRE = "postovulatoire"
    INDETERMINEE = "indeterminee"

class Feu(Enum):
    VERT = "vert"      # union possible (si on évite) / favorable (si on conçoit)
    ORANGE = "orange"  # incertain, prudence
    ROUGE = "rouge"    # fertile

@dataclass
class StatutJour:
    date: date
    phase: Phase
    feu: Feu
    confiance: str          # "haute" | "basse"
    messages: list[str]     # alertes et explications

class MoteurMethode:
    """Interface commune. Chaque méthode implémente sa propre logique."""
    def __init__(self, profil_personnel): ...
    def calculer_statuts(self, observations: list) -> list[StatutJour]: ...
    def fenetre_fertile(self, observations: list) -> tuple: ...
```

Implémentations : `MoteurSensiplan`, `MoteurBillings`, `MoteurCLER`, dans des fichiers séparés (`engines/`).

---

## 4. Modèle de données

```
User(id, email, password_hash, methode, intention,
     heure_reference, mode_decalage, seuil_decalage_min)
     # intention: "eviter" | "concevoir"
     # mode_decalage: "exclusion" | "correction"

Cycle(id, user_id, date_debut_regles, date_fin)

Observation(id, cycle_id, date,
     temp_brute, temp_corrigee, heure_prise, douteux, motif_doute,
     glaire_sensation, glaire_aspect,
     col_hauteur, col_ouverture, col_consistance,
     saignement, union, test_lh)
     # glaire_sensation: "seche" | "humide" | "mouillee_glissante"
     # glaire_aspect: "rien" | "collante_epaisse" | "cremeuse" | "filante_transparente"
     # saignement: "rien" | "leger" | "regles"
     # test_lh: null | "negatif" | "positif"

ProfilPersonnel(user_id, cycle_moyen, cycle_min, cycle_max, ecart_type_cycle,
     jour_ovulation_moyen, temp_plateau_bas, temp_plateau_haut, amplitude_saut,
     heure_prise_habituelle, jour_apparition_glaire_moyen,
     pct_points_douteux, nb_cycles_enregistres)

Statut(observation_id, phase, feu, confiance, messages_json)  # cache du calcul
```

---

## 5. Saisie quotidienne (automatisation maximale)

L'utilisateur saisit **le minimum** ; l'app fait le reste.

- Champ principal : **température** + **heure de prise** (pré-remplie avec l'heure habituelle apprise).
- Observation glaire : sensation + aspect (boutons, pas de texte libre).
- Optionnels repliés : col, test LH, saignement.
- **Union** : case à cocher. Possibilité de **saisir une union pour un jour passé** (la veille notamment), car ça affecte l'interprétation de la glaire du lendemain (sperme résiduel → observation non fiable).
- Bouton « point douteux » + menu motif (fièvre, alcool, sommeil court, voyage, prise décalée…).

### Gestion automatique du décalage horaire
Réglage utilisateur `mode_decalage` :
- **"exclusion"** : si `|heure_prise − heure_reference| > seuil` (défaut 60 min), marquer l'observation `douteux=True`, l'exclure des règles de calcul thermique, mais l'afficher en pointillé sur la courbe.
- **"correction"** : calculer `temp_corrigee = temp_brute − 0,1 × (heures de retard)` (et `+0,1` par heure d'avance). Afficher brute ET corrigée. Utiliser la corrigée dans les calculs.

`heure_reference` : soit fixée par l'utilisateur, soit = médiane des heures de prise du cycle (auto).

---

## 6. MOTEUR SENSIPLAN (à implémenter en premier)

### Indice température — règle « 3 au-dessus de 6 »
1. Exclure les points douteux de la séquence.
2. Trouver 6 températures basses consécutives ; tracer la **ligne de référence** = plus haute des 6.
3. Chercher 3 températures consécutives toutes > ligne de référence.
4. La **3e** doit dépasser la ligne d'au moins **0,2 °C**.
5. **Règle d'exception** : si la 3e ne fait pas +0,2 °C, exiger une **4e** température simplement > ligne (sans seuil).
6. Hausse confirmée le **soir** de cette 3e (ou 4e) température.

### Indice glaire — règle du pic
- **Pic** = dernier jour de glaire de meilleure qualité (`filante_transparente`) ou sensation `mouillee_glissante`.
- Reconnu **rétrospectivement** (confirmé le lendemain quand la qualité régresse).
- Compter 1-2-3 les jours après le pic.

### Combinaison — fin de fertilité (double verrou)
Infertilité postovulatoire confirmée = **soir du jour où les DEUX conditions sont vraies** :
- hausse thermique confirmée (3 ou 4 points hauts), ET
- 3e jour après le pic de glaire atteint.
→ retenir le **plus tardif** des deux.

### Début de fertilité
- Début de cycle : jours infertiles possibles seulement si cycle précédent ovulatoire (règle des 5 jours, prudente).
- Fertilité commence au **plus précoce** de : première glaire/sensation humide, OU `jour_le_plus_court − 8`.

---

## 7. MOTEUR BILLINGS

Aucune température. Logique glaire seule.
- **Règle des jours secs** : après les règles, soirs secs → infertiles. Union le soir, **un jour sur deux** (pour ne pas confondre le sperme avec la glaire) → l'app doit gérer ce « un jour sur deux » en s'appuyant sur le champ `union`.
- Dès apparition de **toute** glaire/sensation humide → fertile (rouge).
- **Pic** = dernier jour de sensation glissante/lubrifiée.
- **Règle du pic** : infertilité postovulatoire = **soir du 3e jour après le pic**.
- Après une union, marquer l'observation glaire du lendemain comme **potentiellement non fiable** (message orange).

---

## 8. MOTEUR CLER — « méthode des trois points hauts » (AVEC COURBE)

Proche de Sensiplan, vocabulaire et tracé CLER.

### Température + courbe (exigence forte)
- Affichage **Chart.js** de la courbe de température du cycle en cours.
- Tracer la **ligne de base** (« ligne des températures basses ») au-dessus de la plus haute des 6 basses.
- Marquer visuellement les **3 points hauts** une fois détectés (points colorés + annotation).
- Marquer le **sommet de glaire** sur l'axe des dates.
- Points douteux affichés différemment (pointillé / autre couleur).

### Règles
- **Trois points hauts** : 3 températures consécutives > 6 précédentes ; la 3e ≥ +0,2 °C au-dessus de la ligne.
- **Sommet de glaire** (« plus beau jour »), reconnu rétrospectivement.
- **Fin de fertilité** = soir du 3e point haut **si** ≥ 3 jours après le sommet ; sinon attendre (logique max(thermique, glaire), comme Sensiplan).
- **Début de fertilité** : `plus_court_cycle − 20` OU apparition de glaire, le plus précoce.

---

## 9. Logique « union » et intention

- **Mode "eviter"** : feu **vert** uniquement en infertilité confirmée (préovulatoire selon règles strictes, ou postovulatoire après double verrou) ; **orange** en doute ; **rouge** en fertilité.
- **Mode "concevoir"** : feu **vert** (= favorable) pendant la fenêtre fertile, surtout jours de glaire filante et autour du pic ; informatif le reste du temps.
- Toujours afficher un **texte d'explication** sous le feu (« pourquoi ce statut »), pas seulement la couleur.

---

## 10. Apprentissage personnalisé (statistiques, PAS de ML)

À **chaque clôture de cycle**, recalculer `ProfilPersonnel` :
- durées de cycle (moy/min/max/écart-type sur 12 derniers),
- jour d'ovulation moyen (déduit du décalage thermique),
- niveaux de plateau bas/haut et amplitude du saut thermique,
- heure de prise habituelle (→ devient `heure_reference` auto),
- jour moyen d'apparition de la glaire fertile,
- % de points douteux et régularité de saisie (→ module la `confiance`).

**Règle de sécurité absolue à respecter dans le code** :
> Le profil personnel sert UNIQUEMENT à anticiper, élargir la prudence et personnaliser les messages/bornes de début de fertilité. Il ne doit JAMAIS raccourcir ni contourner les règles de confirmation (double verrou). Un feu vert reste toujours conditionné aux règles strictes de la méthode, indépendamment de ce que « suggère » l'historique.

Module dédié `apprentissage.py`. Les moteurs reçoivent le profil en entrée et l'utilisent pour les bornes prédictives et les messages, sans toucher aux verrous.

---

## 11. Écrans / routes attendus

- `/` accueil + avertissement obligatoire à la 1re ouverture.
- `/onboarding` choix méthode + intention + réglages décalage.
- `/jour` saisie du jour (formulaire intelligent, champs pré-remplis).
- `/cycle` vue du cycle courant : courbe (Chart.js pour CLER/Sensiplan), feu du jour, explication.
- `/historique` liste des cycles, statistiques du profil.
- `/reglages` méthode, intention, mode décalage, heure de référence.
- `/a-lire` page d'avertissements détaillés + liens vers moniteurs certifiés.

---

## 12. Avertissements (niveau fort)

- Bandeau / page « À lire absolument » à la première ouverture.
- Disclaimer permanent discret en pied de l'écran de verdict.
- Mentionner explicitement : pas un dispositif médical ; efficacité dépendante de l'apprentissage et de la qualité de saisie ; fiabilité réduite en post-partum, allaitement, arrêt de pilule, cycles atypiques ; recommandation de se former auprès d'un moniteur certifié (CLER / Sensiplan / WOOMB-Billings).

---

## 13. Ordre de construction demandé

1. Squelette Flask + modèles + auth + déploiement Render (requirements, Procfile).
2. Onboarding + saisie quotidienne + gestion du décalage horaire.
3. **Moteur Sensiplan** + écran cycle + tests unitaires des règles.
4. Courbe Chart.js + **Moteur CLER**.
5. **Moteur Billings**.
6. Module `apprentissage.py` + ProfilPersonnel.
7. Avertissements + page « À lire ».

Écris des **tests unitaires** pour chaque règle de chaque moteur (cas nominal, point douteux exclu, règle d'exception thermique, pic mal placé). C'est la partie critique : une erreur de règle peut produire un faux feu vert.

Commence par l'étape 1 et montre-moi la structure du projet avant de continuer.
