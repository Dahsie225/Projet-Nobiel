# 🛠️ Système d'Administration - NOBIEL

## Vue d'ensemble

Le système d'administration de NOBIEL offre une interface complète pour gérer :

1. **Gestion des Adhésions** 📋
   - Lister toutes les adhésions
   - Approuver/rejeter les adhésions en attente
   - Modifier les détails des adhésions
   - Exporter les données en CSV

2. **Actualités** 📰
   - Créer et modifier des articles
   - Publier ou mettre en brouillon
   - Classer par catégorie
   - Supprimer les articles

3. **Annuaire (Gestion des Membres)** 👥
   - Voir tous les membres
   - Chercher et filtrer par statut/ville
   - Modifier les informations des membres
   - Activer/désactiver les membres

4. **Paiements** 💳
   - Gérer les paiements des adhésions
   - Marquer comme payé/en attente
   - Générer des rapports par méthode et type
   - Suivre les revenus

## Accès

### URL
```
http://localhost:5000/admin
```

### Authentification
- **Utilisateur par défaut**: `admin`
- **Mot de passe par défaut**: `admin123`
- ⚠️ **À CHANGER EN PRODUCTION!**

### Rôles d'accès
- `admin`: Accès complet à toutes les fonctionnalités
- `moderator`: Accès limité aux fonctionnalités de modération
- `user`: Aucun accès à l'admin

## Initialisation

### 1. Créer la base de données
```bash
python init_database.py
```

Cela va :
- Créer toutes les tables
- Créer un administrateur par défaut (admin/admin123)

### 2. Lancer l'application
```bash
python run.py
```

### 3. Accéder au tableau de bord
- Allez à http://localhost:5000
- Cliquez sur "Connexion"
- Identifiant: `admin`
- Mot de passe: `admin123`

## Routes d'administration

### Dashboard
```
GET /admin/
```
Tableau de bord avec statistiques générales.

### Adhésions
```
GET /admin/adhesions              # Lister
POST /admin/adhesions/<id>/approve # Approuver
POST /admin/adhesions/<id>/reject  # Rejeter
GET /admin/adhesions/<id>/edit     # Éditer
GET /admin/adhesions/export        # Exporter CSV
```

### Articles
```
GET /admin/articles                           # Lister
GET /admin/articles/new                       # Créer
POST /admin/articles/new                      # Créer (POST)
GET /admin/articles/<id>/edit                 # Éditer
POST /admin/articles/<id>/edit                # Éditer (POST)
POST /admin/articles/<id>/delete              # Supprimer
```

### Membres
```
GET /admin/members                            # Lister
GET /admin/members/<id>                       # Voir
GET /admin/members/<id>/edit                  # Éditer
POST /admin/members/<id>/edit                 # Éditer (POST)
POST /admin/members/<id>/activate             # Activer
POST /admin/members/<id>/deactivate           # Désactiver
```

### Paiements
```
GET /admin/payments                           # Lister
POST /admin/payments/<id>/mark-paid           # Marquer comme payé
POST /admin/payments/<id>/mark-pending        # Marquer comme en attente
GET /admin/payments/report                    # Rapport
```

### Statistiques (API)
```
GET /admin/api/stats                          # JSON de statistiques
```

## Fonctionnalités principales

### Tableau de bord
- Vue d'ensemble avec 4 cartes de statistiques
- Articles récents
- Adhésions récentes
- Boutons d'accès rapide

### Adhésions
- Filtrage par statut (tous, en attente, payées, annulées)
- Actions rapides (approuver, éditer)
- Export en CSV
- Pagination

### Articles
- Filtrage par statut (tous, publiés, brouillons)
- Création/modification avec validation
- Publication planifiée
- Suppression avec confirmation

### Annuaire
- Recherche par nom/email/ville
- Filtrage par statut d'adhésion
- Activation/désactivation
- Statistiques d'adhésion
- Vue détaillée avec historique des adhésions

### Paiements
- Statistiques globales
- Filtres par statut et méthode
- Rapports par période (mois, année, 30 jours)
- Analyse par méthode et type
- Détail des paiements avec dates

## Sécurité

### Contrôle d'accès
- Vérification du rôle sur chaque route
- Redirection en cas d'accès non autorisé
- Flash messages pour l'utilisateur

### Protection
- CSRF protection (via Flask-WTF)
- Validation des données
- Hachage des mots de passe (Werkzeug)

### Recommandations
1. **Changez le mot de passe admin** immédiatement
2. **Configurez FLASK_SECRET** unique en production
3. **Utilisez HTTPS** en production
4. **Limitez les accès** par IP si possible
5. **Sauvegardez régulièrement** la base de données

## Modifications personnalisées

### Ajouter un utilisateur admin
```python
from app import create_app, db
from app.models.models import User

app = create_app()
with app.app_context():
    user = User(
        username='newadmin',
        email='newadmin@example.com',
        full_name='New Admin',
        role='admin'
    )
    user.set_password('password_secure')
    db.session.add(user)
    db.session.commit()
```

### Modifier les permissionsParlez avec l'administrateur au sujet des droits d'accès via les rôles dans le modèle `User`.

### Personnaliser les templates
- Modifiez les fichiers dans `app/templates/admin/`
- Respectez la structure Bootstrap existante

## Dépannage

### "Accès refusé"
- Vérifiez que vous êtes connecté
- Vérifiez votre rôle (utilisateur régulier vs admin)
- Reconnecter-vous

### Erreur de base de données
- Exécutez `python init_database.py`
- Vérifiez la connexion MySQL
- Vérifiez les droits d'accès à la base

### Les données ne s'enregistrent pas
- Vérifiez la console pour les erreurs SQL
- Vérifiez les permissions MySQL
- Assurez-vous que la base n'est pas pleine

## Support

Pour les bugs ou demandes de fonctionnalités, consultez la documentation du projet ou contactez l'administrateur système.
