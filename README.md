# RNN App — Régulation Naturelle des Naissances

Application web Flask pour accompagner un couple dans la pratique de la RNN (Sensiplan, Billings, CLER).

## Prérequis

- Python 3.11+
- pip

## Installation locale

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask db upgrade
python run.py
```

→ http://localhost:5000

## Fonctionnalités

### Comptes utilisateurs
- Inscription avec validation e-mail
- Un espace privé par couple (données isolées par `user_id`)

### Méthodes supportées
| Méthode | Moteur | Température | Courbe |
|---------|--------|-------------|--------|
| Sensiplan | `MoteurSensiplan` | Oui | Chart.js |
| CLER | `MoteurCLER` | Oui | Chart.js |
| Billings | `MoteurBillings` | Non | — |

### Règles implémentées
- **Sensiplan** : 3 au-dessus de 6, pic de glaire, double verrou, règle des 5 jours
- **CLER** : trois points hauts, sommet de glaire, début `cycle_min − 20`
- **Billings** : jours secs, pic glissante, union veille non fiable
- **Décalage horaire** : exclusion ou correction ± 0,1 °C/h
- **Apprentissage** : statistiques sur cycles clôturés (jamais pour raccourcir les verrous)

### Écrans
- `/` — Accueil + verdict du jour
- `/onboarding` — Configuration initiale
- `/jour` — Saisie quotidienne + verdict
- `/cycle` — Courbe, journal, feu du jour
- `/historique` — Cycles clôturés, profil personnel
- `/reglages` — Méthode, intention, décalage
- `/a-lire` — Avertissements détaillés

## Tests

```bash
pytest tests/ -v
```

28 tests couvrant auth, décalage, saisie et les trois moteurs.

## Structure

```
app/
  auth/           # Inscription, connexion, e-mail
  main/           # Routes et formulaires
  engines/        # Sensiplan, CLER, Billings
  services/       # Cycles, décalage, statuts, apprentissage
  models.py
run.py
```

## Déploiement Render (Blueprint)

Le fichier `render.yaml` provisionne **tout en un clic** : Web Service + PostgreSQL + migrations.

```
GitHub → Render Dashboard → New → Blueprint → Apply
```

Guide détaillé : **[DEPLOY.md](DEPLOY.md)**

Après déploiement, configurer `MAIL_*` dans le dashboard Render pour les e-mails de validation.

## Avertissement

Cette application n'est pas un dispositif médical. Formation auprès d'un moniteur certifié indispensable.
