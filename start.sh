#!/usr/bin/env bash
# Démarrage Render (plan gratuit : pas de preDeployCommand)
set -o errexit

echo "→ Mise à jour de la base de données…"
flask db upgrade

echo "→ Démarrage de Gunicorn…"
exec gunicorn --bind "0.0.0.0:${PORT:-5000}" --workers 2 --timeout 120 run:app
