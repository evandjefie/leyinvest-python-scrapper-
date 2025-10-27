-- Script d'initialisation de la base de données BRVM

-- Utiliser la base de données
USE brvm_db;

-- Définir le charset par défaut
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Table actions
CREATE TABLE IF NOT EXISTS actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbole VARCHAR(10) NOT NULL UNIQUE,
    nom VARCHAR(255) NOT NULL,
    volume INT DEFAULT 0,
    cours_veille FLOAT,
    cours_ouverture FLOAT,
    cours_cloture FLOAT,
    variation FLOAT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbole (symbole),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table historique_actions
CREATE TABLE IF NOT EXISTS historique_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbole VARCHAR(10) NOT NULL,
    data_snapshot JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbole (symbole),
    INDEX idx_created_at (created_at),
    INDEX idx_symbole_date (symbole, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table indicateurs_marche
CREATE TABLE IF NOT EXISTS indicateurs_marche (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_rapport DATE NOT NULL UNIQUE,
    taux_rendement_moyen FLOAT,
    per_moyen FLOAT,
    taux_rentabilite_moyen FLOAT,
    prime_risque_marche FLOAT,
    source_pdf VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date_rapport (date_rapport),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table webhook_subscriptions
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(512) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_triggered DATETIME,
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion de données de test (optionnel)
-- Décommenter si vous voulez des données de test

-- INSERT INTO actions (symbole, nom, volume, cours_veille, cours_ouverture, cours_cloture, variation) VALUES
-- ('BICC', 'BICI Côte d''Ivoire', 15000, 7500, 7520, 7550, 0.67),
-- ('ETIT', 'Ecobank Transnational Inc.', 25000, 18.50, 18.60, 18.80, 1.62),
-- ('SDCC', 'SODE CI', 8000, 4200, 4180, 4150, -1.19);

-- INSERT INTO indicateurs_marche (date_rapport, taux_rendement_moyen, per_moyen, taux_rentabilite_moyen, prime_risque_marche, source_pdf) VALUES
-- (CURDATE(), 7.36, 12.78, 8.64, 2.11, 'https://www.brvm.org/sites/default/files/boc_20251022_2.pdf');

-- Afficher les tables créées
SHOW TABLES;

-- Message de confirmation
SELECT 'Base de données BRVM initialisée avec succès!' AS message;
