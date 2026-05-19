-- Script d'initialisation de la base de données NOBIEL
-- Exécutez ceci dans phpMyAdmin ou en ligne de commande MySQL

CREATE DATABASE IF NOT EXISTS nobiel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nobiel;

-- Les tables seront créées automatiquement par SQLAlchemy au premier lancement
-- Voir le fichier run.py et app/__init__.py

-- Vous pouvez aussi créer un utilisateur dédié (optionnel) :
-- CREATE USER 'nobiel_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
-- GRANT ALL PRIVILEGES ON nobiel.* TO 'nobiel_user'@'localhost';
-- FLUSH PRIVILEGES;
