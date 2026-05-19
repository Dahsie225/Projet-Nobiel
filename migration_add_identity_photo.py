#!/usr/bin/env python
"""Script pour ajouter la colonne identity_photo à la table members"""
from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    try:
        # Exécuter la commande SQL pour ajouter la colonne
        db.session.execute(text("""
            ALTER TABLE members 
            ADD COLUMN identity_photo VARCHAR(255) AFTER birthdate
        """))
        db.session.commit()
        print("✅ Colonne 'identity_photo' ajoutée avec succès à la table 'members'!")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.session.rollback()
