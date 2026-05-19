# 🎯 NOBIEL - Plateforme Associative Numérique

**NOBIEL** est une plateforme web moderne conçue pour centraliser les activités et gérer efficacement les membres d'une association.

## 📖 Table des Matières
- [Fonctionnalités](#fonctionnalités)
- [Stack Technologique](#stack-technologique)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du Projet](#structure-du-projet)
- [API Routes](#api-routes)
- [Base de Données](#base-de-données)

---

## ✨ Fonctionnalités

### 1. **Page d'Accueil** 🏠
- Vue d'ensemble de l'association
- Statistiques (membres, articles, événements)
- Présentation des fonctionnalités clés
- Appel à l'action (Adhérer, Actualités, etc.)

### 2. **Gestion des Actualités** 📰
- **Création d'articles** : Rédacteurs autorités peuvent publiquer des actualités
- **Catégories** : Actualités, Événements, Annonces
- **Brouillons** : Sauvegarde avant publication
- **Édition & Suppression** : Modifiez ou supprimez vos articles
- **Pagination** : Affichage optimisé des listes

### 3. **Authentification Utilisateur** 🔐
- Inscription avec validation email
- Connexion sécurisée (mot de passe hashé)
- Rôles : Admin, Modérateur, Utilisateur
- Session persistante (7 jours par défaut)
- Reset de mot de passe (à implémenter)

### 4. **Gestion des Adhésions** 💳
- Formulaire simplifié d'adhésion
- Types d'adhésion : Étudiant, Professionnel, Partenaire, Donateur
- Suivi des cotisations (Annuelle, Mensuelle, À vie)
- Méthodes de paiement : Orange Money, Wave, MTN, Virement
- Validation des paiements par administrateur
- Statut d'adhésion : Actif, En attente, Inactif

### 5. **Annuaire des Membres** 👥
- Répertoire consultable des membres actifs
- Recherche par nom/email/région
- Filtrage par ville/région
- Pagination
- Profils membres détaillés
- (Accès restreint aux utilisateurs connectés)

### 6. **Tableau de Bord Administrateur** 📊
- Gestion centralisée des articles
- Validation des adhésions
- Vue d'ensemble des statistiques
- Gestion des utilisateurs (à implémenter)

---

## 🛠️ Stack Technologique

### Backend
- **Python 3.7+**
- **Flask** 2.3.3 - Microframework web léger
- **SQLAlchemy** - ORM pour gestion BD
- **Flask-Login** - Gestion d'authentification
- **WTForms** - Validation de formulaires
- **Flask-WTF** - Protection CSRF

### Frontend
- **HTML5**
- **CSS3** (Responsive Design)
- **JavaScript** vanilla
- **Jinja2** - Templating

### Base de Données
- **MySQL 5.7+** (via WAMP)
- **PyMySQL** - Driver Python-MySQL

### Outils
- **pip** - Gestionnaire de paquets Python
- **git** - Contrôle de version
- **VS Code** - Éditeur de code

---

## 📦 Installation

### Prérequis
- Python 3.7 ou supérieur installé
- WAMP64 avec MySQL activé
- Git (optionnel)

### Étapes

#### 1. **Créer l'environnement virtuel**
```bash
cd c:\wamp64\www\Projets\NOBIEL
python -m venv env
# ou avec virtualenv :
# virtualenv env

# Activez l'environnement
env\Scripts\activate  # Windows
# source env/bin/activate  # Linux/Mac
```

#### 2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

#### 3. **Démarrer WAMP**
- Ouvrez `C:\wamp64\wampmanager.exe`
- Attendez que tous les services deviennent **VERTS**
- Vérifiez : http://localhost (page WAMP)

#### 4. **Créer la base de données**
- Allez à http://localhost/phpmyadmin
- Créez une nouvelle base nommée `nobiel`
- Caractères : UTF-8 (`utf8mb4_unicode_ci`)

#### 5. **Initialiser les tables**
```bash
python init_database.py
```

Vous devriez voir :
```
🔄 Création des tables...
✅ Base de données initialisée avec succès !
📊 Tables créées :
   - users
   - members
   - articles
   - adhesions
```

#### 6. **Lancer l'application**
```bash
python run.py
```

Rendez-vous à **http://localhost:5000** ! 🎉

---

## 🚀 Utilisation

### Créer un compte administrateur
```bash
# (À implémenter - pour l'instant, créez un compte via le formulaire)
# et mettez manuellement le rôle à 'admin' via phpMyAdmin
```

### Workflow Typique

1. **Visiteur** → Page d'accueil → Adhérer
2. **Adhérent** → Créer compte → Accès annuaire
3. **Admin** → Gérer articles, valider attributions, etc.

---

## 📂 Structure du Projet

```
NOBIEL/
├── app/
│   ├── __init__.py           # Initialisation Flask
│   ├── models/
│   │   └── models.py         # Modèles de données (ORM)
│   ├── routes/
│   │   ├── main.py           # Routes principales (accueil, about, contact)
│   │   ├── auth.py           # Routes authentification
│   │   ├── articles.py       # Routes actualités (CRUD)
│   │   └── members.py        # Routes membres & adhésions
│   ├── templates/
│   │   ├── base.html         # Template de base
│   │   ├── index.html        # Accueil
│   │   ├── about.html        # À propos
│   │   ├── contact.html      # Contact
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── articles/
│   │   │   ├── list.html
│   │   │   ├── view.html
│   │   │   └── edit.html
│   │   └── members/
│   │       ├── list.html     # Annuaire
│   │       ├── view.html     # Profil membre
│   │       ├── join.html     # Formulaire adhésion
│   │       └── adhesions.html # Gestion adhésions
│   └── static/
│       ├── css/
│       │   └── style.css     # Styles principaux
│       ├── js/
│       │   └── main.js       # Scripts JavaScript
│       └── images/           # Images du site
│
├── run.py                    # Point d'entrée
├── config.py                 # Configuration Flask
├── requirements.txt          # Dépendances Python
├── init_database.py          # Script d'initialisation BD
├── .env                      # Variables d'environnement
├── init_db.sql               # Script SQL optionnel
├── GUIDE_DEMARRAGE.md        # Guide rapide
└── README.md                 # Cette documentation

```

---

## 🔗 Routes API

### Navigation Publique
| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Page d'accueil |
| `/about` | GET | À propos |
| `/contact` | GET/POST | Page contact |

### Authentification
| Route | Méthode | Description |
|-------|---------|-------------|
| `/auth/login` | GET/POST | Connexion |
| `/auth/register` | GET/POST | Inscription |
| `/auth/logout` | GET | Déconnexion |

### Actualités
| Route | Méthode | Description |
|-------|---------|-------------|
| `/articles/` | GET | Liste articles |
| `/articles/<slug>` | GET | Voir article |
| `/articles/new` | GET/POST | Créer article |
| `/articles/<id>/edit` | GET/POST | Modifier article |
| `/articles/<id>/delete` | POST | Supprimer article |

### Membres
| Route | Méthode | Description |
|-------|---------|-------------|
| `/members/` | GET | Annuaire publicité |
| `/members/<id>` | GET | Profil membre |
| `/members/join` | GET/POST | Formulaire adhésion |
| `/members/<id>/adhesions` | GET/POST | Gérer adhésions |

---

## 🗄️ Base de Données

### Tables
1. **users** - Utilisateurs (Admin, Modérateurs)
2. **members** - Membres/Adhérents
3. **articles** - Actualités/Articles
4. **adhesions** - Historique des cotisations

### Schéma Relationnel
```
users
├── articles (1:N) → articles.author_id

members
└── adhesions (1:N) → adhesions.member_id
```

### Exemple de Requête
```sql
-- Adhérents actifs par ville
SELECT m.first_name, m.last_name, m.city, a.start_date
FROM members m
LEFT JOIN adhesions a ON m.id = a.member_id
WHERE m.membership_status = 'active'
ORDER BY m.city;
```

---

## 🔒 Sécurité

### Implémenté ✅
- Mots de passe hashés (Werkzeug)
- Protection CSRF (Flask-WTF)
- Validation des formulaires (WTForms)
- Sessions sécurisées (Flask-Login)

### À Implémenter ⏳
- Rate limiting sur login
- 2FA (Two-Factor Authentication)
- Audit logs
- Chiffrement des données sensibles
- HTTPS en production

---

## 🐛 Troubleshooting

### "Connection refused" (MySQL)
→ Démarrez WAMP : `C:\wamp64\wampmanager.exe`

### "Access Denied for user 'root'@'localhost'"
→ Vérifiez les IDs MySQL dans `config.py`

### "Base de données n'existe pas"
→ Créez-la via phpMyAdmin

### 404 sur les pages
→ Vérifiez que les blueprints sont enregistrés dans `app/__init__.py`

---

## 📝 Licence
MIT License - Libre d'utilisation

## 👨‍💻 Contributeurs
Développé pour l'Association NOBIEL - 2026

---

## 📞 Support
Pour toute question, contactez : contact@nobiel.ci

**Bonne utilisation ! 🚀**
