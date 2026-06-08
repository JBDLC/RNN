# Déploiement sur Render (Blueprint)

Ce dépôt inclut un **Blueprint Render** (`render.yaml`) qui provisionne tout automatiquement :

- Service Web Python (Gunicorn)
- Base PostgreSQL
- Variables d'environnement (`SECRET_KEY`, `DATABASE_URL`, `FLASK_APP`…)
- **Migrations** (`flask db upgrade`) à chaque déploiement

## Étapes

### 1. Pousser le code sur GitHub

```bash
git init
git add .
git commit -m "RNN App — déploiement Render"
git remote add origin https://github.com/VOTRE_COMPTE/19-RNN.git
git push -u origin main
```

### 2. Créer le Blueprint sur Render

1. Aller sur [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Blueprint**
3. Connecter le dépôt GitHub `19-RNN`
4. Render détecte `render.yaml` et affiche les ressources à créer :
   - `rnn-app` (Web Service)
   - `rnn-db` (PostgreSQL)
5. Cliquer **Apply** — le premier déploiement démarre (build + migrations + démarrage)

### 3. Après le déploiement

L'URL de l'app est du type `https://rnn-app-xxxx.onrender.com`.

`BASE_URL` est remplie automatiquement via `RENDER_EXTERNAL_URL` (liens de vérification e-mail).

#### Configurer l'e-mail (obligatoire pour la validation de compte)

Dans le dashboard Render → service **rnn-app** → **Environment** :

| Variable | Exemple |
|----------|---------|
| `MAIL_SERVER` | `smtp.gmail.com` |
| `MAIL_USERNAME` | `votre@gmail.com` |
| `MAIL_PASSWORD` | mot de passe d'application |
| `MAIL_DEFAULT_SENDER` | `votre@gmail.com` |

Puis **Save Changes** (redéploiement automatique).

### 4. Vérifier

- `https://votre-app.onrender.com/health` → `{"status":"ok"}`
- Créer un compte → recevoir l'e-mail de confirmation

## Ce qui se passe à chaque déploiement

```
pip install -r requirements.txt     ← buildCommand
flask db upgrade                    ← preDeployCommand (crée/met à jour les tables)
gunicorn run:app                    ← startCommand
```

## Plan gratuit Render

- Le service Web **s'endort** après ~15 min d'inactivité (réveil en ~30 s)
- PostgreSQL gratuit : 1 Go, expire après 90 jours (renouvelable)

## Dépannage

| Problème | Solution |
|----------|----------|
| Build échoue sur `flask db upgrade` | Vérifier que `DATABASE_URL` est liée à `rnn-db` dans Environment |
| E-mails non envoyés | Configurer `MAIL_*` ; consulter les logs Render |
| Erreur 502 au réveil | Normal sur le plan gratuit, réessayer après quelques secondes |

## Fichiers de déploiement

| Fichier | Rôle |
|---------|------|
| `render.yaml` | Blueprint (infra complète) |
| `Procfile` | Commande de démarrage (fallback) |
| `requirements.txt` | Dépendances Python |
| `migrations/` | Schéma PostgreSQL (Alembic) |
| `.python-version` | Python 3.11.9 |
