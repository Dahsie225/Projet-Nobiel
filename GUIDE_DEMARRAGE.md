# 🚀 Guide de Démarrage - NOBIEL

## Prérequis
- ✅ Python 3.7+ (activé)
- ✅ WAMP64 (MySQL + Apache)
- ✅ Dépendances Flask installées

## Étapes de démarrage

### 1️⃣ Démarrer WAMP
- Ouvrez le dossier `C:\wamp64`
- Double-cliquez sur `wampmanager.exe`
- Attendez que l'icône devienne **VERTE** (tous services actifs)
- Vérifiez : http://localhost (page WAMP doit s'afficher)

### 2️⃣ Créer la base de données
- Allez à http://localhost/phpmyadmin
- Cliquez sur "Nouvelle" (ou "New")
- Entrez `nobiel` comme nom
- Cliquez sur "Créer"

### 3️⃣ Initialiser les tables
```bash
cd c:\wamp64\www\Projets\NOBIEL
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

### 4️⃣ Lancer l'application
```bash
cd c:\wamp64\www\Projets\NOBIEL
python run.py
```

Vous verrez :
```
 * Running on http://127.0.0.1:5000
```

Ouvrez http://localhost:5000 dans votre navigateur ! 🎉

## ⚠️ Problèmes courants

**"Connection refused"**
→ WAMP n'est pas démarré. Exécutez wampmanager.exe

**"Access Denied for user"**
→ Le mot de passe MySQL est incorrect dans config.py

**"Base de données n'existe pas"**
→ Créez la base via phpMyAdmin (étape 2)

## Structure du projet
```
NOBIEL/
├── app/
│   ├── models/          (Modèles de données)
│   ├── routes/          (Routage / Logique)
│   ├── templates/       (Pages HTML)
│   └── static/          (CSS, JS, Images)
├── run.py               (Lancer l'app)
├── config.py            (Configuration)
├── requirements.txt     (Dépendances)
└── init_database.py     (Initialiser DB)
```

Bon développement ! 🚀
