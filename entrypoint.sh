#!/bin/sh
set -e

echo "==> Initialisation des tables de la base de données..."
python -c "
from run import app
from app import db
with app.app_context():
    db.create_all()
    print('Tables créées (ou déjà existantes).')
"

echo "==> Démarrage de Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
