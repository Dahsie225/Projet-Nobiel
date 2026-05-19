#!/usr/bin/env python
"""
Script pour initialiser la base de données
Crée les tables et ajoute un administrateur par défaut
Usage: python init_database.py
"""

import os
import sys
from app import create_app, db
from app.models.models import User

def init_database():
    """Crée toutes les tables de la base de données"""
    app = create_app(config_name=os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("🔄 Création des tables...")
        db.create_all()
        print("✅ Base de données initialisée avec succès !")
        print("\n📊 Tables créées :")
        
        # Affiche les tables créées
        inspector = db.inspect(db.engine)
        for table in inspector.get_table_names():
            print(f"   - {table}")
        
        # Vérifie si un admin existe
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("\n🔐 Création d'un administrateur par défaut...")
            admin = User(
                username='admin',
                email='admin@nobiel.ci',
                full_name='Administrateur NOBIEL',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')  # À changer!!
            db.session.add(admin)
            db.session.commit()
            print("✓ Administrateur créé!")
            print("  Identifiant: admin")
            print("  Mot de passe: admin123")
            print("  ⚠️  CHANGEZ LE MOT DE PASSE EN PRODUCTION!\n")
        else:
            print("ℹ️  Un administrateur existe déjà.\n")

if __name__ == '__main__':
    init_database()

