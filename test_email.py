#!/usr/bin/env python
"""
Script de test pour vérifier que Flask-Mail fonctionne correctement.
Usage : python test_email.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.models import Member, Article, User, NewsletterSubscription
from app.email_utils import send_member_welcome, send_member_activated, send_adhesion_approved, send_newsletter_notification
from datetime import datetime, timedelta

def test_emails():
    """Lance une série de tests d'emails"""
    app = create_app('development')
    
    with app.app_context():
        print("=" * 60)
        print("TEST FLASK-MAIL — NOBIEL")
        print("=" * 60)
        
        # Config
        print(f"\n📧 Configuration SMTP :")
        print(f"   Serveur   : {app.config['MAIL_SERVER']}")
        print(f"   Port      : {app.config['MAIL_PORT']}")
        print(f"   TLS       : {app.config['MAIL_USE_TLS']}")
        print(f"   Username  : {app.config['MAIL_USERNAME']}")
        print(f"   Supprimé  : {app.config['MAIL_SUPPRESS_SEND']}")
        
        if app.config['MAIL_SUPPRESS_SEND']:
            print("\n⚠️  MAIL_USERNAME vide → emails supprimés localement (normal en dev)")
            return
        
        print("\n" + "=" * 60)
        print("TEST 1 : Email de bienvenue (nouvel adhérent)")
        print("=" * 60)
        try:
            # Créer un test member
            test_member = Member(
                first_name="Test",
                last_name="User",
                email=os.environ.get('MAIL_USERNAME', ''),
                city="Abidjan",
                membership_type="student",
                membership_status="pending"
            )
            send_member_welcome(test_member)
            print("✅ Email de bienvenue envoyé")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        print("\n" + "=" * 60)
        print("TEST 2 : Email d'activation (adhésion validée)")
        print("=" * 60)
        try:
            test_member.membership_status = 'active'
            send_member_activated(test_member)
            print("✅ Email d'activation envoyé")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        print("\n" + "=" * 60)
        print("TEST 3 : Email de notification newsletter")
        print("=" * 60)
        try:
            # Créer un test article
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                print("⚠️  Pas d'admin trouvé, création d'un admin de test...")
                admin_user = User(
                    username="test_admin",
                    email="test_admin@nobiel.ci",
                    role="admin",
                    is_active=True
                )
                admin_user.set_password("TestPassword123")
                db.session.add(admin_user)
                db.session.commit()
            
            test_article = Article(
                title="Test — Ceci est un article de test",
                slug="test-article",
                content="Ceci est le contenu d'un article de test pour tester la newsletter.",
                excerpt="Un bref résumé du test",
                category="announcement",
                author_id=admin_user.id,
                is_published=True,
                published_at=datetime.utcnow()
            )
            
            # S'assurer qu'il y a au moins un subscriber de test
            sub = NewsletterSubscription.query.filter_by(email=os.environ.get('MAIL_USERNAME', '')).first()
            if not sub:
                sub = NewsletterSubscription(email=os.environ.get('MAIL_USERNAME', ''))
                db.session.add(sub)
                db.session.commit()
            
            send_newsletter_notification(test_article)
            print("✅ Email de notification newsletter envoyé")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        print("\n" + "=" * 60)
        print("✨ Tests terminés")
        print("=" * 60)
        print("\n💡 Vérifiez votre boîte Gmail (et dossier Spam)")
        print(f"   Email destinataire : {os.environ.get('MAIL_USERNAME', '')}")


if __name__ == '__main__':
    test_emails()
