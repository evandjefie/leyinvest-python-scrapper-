# 📊 BRVM Data API

API FastAPI professionnelle pour le scraping automatique des cours des actions BRVM et l'extraction des indicateurs de marché depuis les bulletins officiels PDF.

## 🎯 Fonctionnalités

- ✅ **Scraping automatique** des cours des actions BRVM toutes les 30 minutes
- ✅ **Extraction PDF** des indicateurs de marché (12h et 18h chaque jour)
- ✅ **Base de données MySQL** avec 3 tables (actions, historique, indicateurs)
- ✅ **API REST complète** documentée avec Swagger
- ✅ **Webhooks** pour notifications en temps réel
- ✅ **Scheduler APScheduler** pour tâches automatiques
- ✅ **Logs détaillés** avec rotation
- ✅ **Docker & Docker Compose** pour déploiement facile
- ✅ **Compatible Render** pour hébergement cloud

## 📁 Structure du projet

```
brvm-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application FastAPI principale
│   ├── config.py               # Configuration centralisée
│   ├── database.py             # Gestion base de données
│   ├── models.py               # Modèles SQLAlchemy
│   ├── schemas.py              # Schémas Pydantic
│   ├── api/
│   │   ├── routes/
│   │   │   ├── actions.py      # Routes actions
│   │   │   ├── historique.py   # Routes historique
│   │   │   ├── indicateurs.py  # Routes indicateurs
│   │   │   └── webhooks.py     # Routes webhooks
│   ├── services/
│   │   ├── scraper.py          # Scraper BRVM
│   │   ├── pdf_extractor.py    # Extracteur PDF
│   │   ├── webhook_manager.py  # Gestionnaire webhooks
│   │   └── scheduler.py        # Planificateur tâches
│   └── utils/
│       └── logger.py           # Système de logs
├── downloads/                   # PDF téléchargés
├── logs/                        # Fichiers de logs
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Installation

### Prérequis

- Python 3.12+
- MySQL 8.0+
- Docker & Docker Compose (optionnel)

### Option 1: Installation locale

```bash
# Cloner le projet
git clone <repository-url>
cd brvm-api

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations

# Créer les répertoires nécessaires
mkdir -p downloads logs

# Lancer l'application
python -m uvicorn app.main:app --reload
```

### Option 2: Docker Compose (recommandé)

```bash
# Cloner le projet
git clone <repository-url>
cd brvm-api

# Configurer les variables d'environnement
cp .env.example .env

# Lancer avec Docker Compose
docker-compose up -d

# Voir les logs
docker-compose logs -f api

# Arrêter
docker-compose down
```

## 📖 Configuration

### Variables d'environnement (.env)

```bash
# Application
APP_NAME=BRVM Data API
DEBUG=False
LOG_LEVEL=INFO

# Base de données
DATABASE_URL=mysql+pymysql://brvm_user:brvm_password@localhost:3306/brvm_db
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=brvm_db
MYSQL_USER=brvm_user
MYSQL_PASSWORD=brvm_password

# Scheduler
SCRAPER_INTERVAL_MINUTES=30    # Fréquence scraping
PDF_DOWNLOAD_HOURS=[12, 18]    # Heures extraction PDF

# Timezone
TIMEZONE=Africa/Abidjan
```

## 🌐 Documentation API

Une fois l'application lancée, accédez à:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Endpoints principaux

#### 📊 Actions

- `GET /api/actions` - Liste des actions (pagination + filtres)
- `GET /api/actions/{symbole}` - Détails d'une action
- `GET /api/actions/top/volume` - Top actions par volume
- `GET /api/actions/top/variation` - Top actions par variation

#### 📜 Historique

- `GET /api/historique` - Historique des snapshots
- `GET /api/historique/{symbole}` - Historique d'une action
- `GET /api/historique/{symbole}/latest` - Dernier snapshot

#### 📈 Indicateurs

- `GET /api/indicateurs` - Liste des indicateurs
- `GET /api/indicateurs/latest` - Dernier indicateur
- `GET /api/indicateurs/date/{date}` - Indicateur par date
- `GET /api/indicateurs/range` - Indicateurs sur une période
- `GET /api/indicateurs/stats/summary` - Résumé statistique

#### 🔔 Webhooks

- `POST /api/webhooks/register` - Enregistrer un webhook
- `GET /api/webhooks` - Liste des webhooks
- `DELETE /api/webhooks/{id}` - Supprimer un webhook
- `PATCH /api/webhooks/{id}/toggle` - Activer/Désactiver
- `POST /api/webhooks/test-push` - Tester les webhooks

#### ⚙️ Système

- `GET /` - Informations API
- `GET /health` - Health check
- `GET /scheduler/status` - Statut du planificateur
- `POST /scheduler/trigger/{job_id}` - Déclencher une tâche

## 🔄 Tâches automatiques

### Tâche 1: Scraping BRVM
- **Fréquence**: Toutes les 30 minutes (configurable)
- **Action**: Récupère les cours depuis https://www.brvm.org/fr/cours-actions/0
- **Résultat**: Met à jour la table `actions` et crée des snapshots

### Tâche 2: Extraction PDF
- **Fréquence**: Chaque jour à 12h et 18h
- **Action**: Télécharge et extrait les indicateurs du bulletin PDF
- **Résultat**: Met à jour la table `indicateurs_marche`
- **Nettoyage**: Supprime automatiquement les données du mois précédent le 1er de chaque mois

## 🔔 Webhooks

### Format du payload

```json
{
  "timestamp": "2025-10-24T12:00:00Z",
  "source": "BRVM",
  "type": "update",
  "data_type": "indicateurs_marche",
  "data": {
    "taux_rendement_moyen": 7.36,
    "per_moyen": 12.78,
    "taux_rentabilite_moyen": 8.64,
    "prime_risque_marche": 2.11
  }
}
```

### Enregistrer un webhook

```bash
curl -X POST "http://localhost:8000/api/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook",
    "description": "Mon webhook"
  }'
```

## 🗄️ Base de données

### Table: actions

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT (PK, AI) | Identifiant |
| symbole | VARCHAR(10) | Code BRVM |
| nom | VARCHAR(255) | Nom complet |
| volume | INT | Volume échangé |
| cours_veille | FLOAT | Cours veille |
| cours_ouverture | FLOAT | Cours ouverture |
| cours_cloture | FLOAT | Cours clôture |
| variation | FLOAT | Variation % |
| updated_at | DATETIME | Date MAJ |

### Table: historique_actions

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT (PK, AI) | Identifiant |
| symbole | VARCHAR(10) | Code |
| data_snapshot | JSON | Données snapshot |
| created_at | DATETIME | Date snapshot |

### Table: indicateurs_marche

| Colonne | Type | Description |
|---------|------|-------------|
| id | INT (PK, AI) | Identifiant |
| date_rapport | DATE | Date rapport |
| taux_rendement_moyen | FLOAT | Taux rendement |
| per_moyen | FLOAT | PER moyen |
| taux_rentabilite_moyen | FLOAT | Taux rentabilité |
| prime_risque_marche | FLOAT | Prime de risque |
| source_pdf | VARCHAR(255) | URL PDF |
| created_at | DATETIME | Date insertion |

## 📝 Logs

Les logs sont enregistrés dans `logs/app.log` avec rotation automatique:
- Taille maximale: 10 MB
- Fichiers conservés: 5
- Format: `YYYY-MM-DD HH:MM:SS - module - LEVEL - function:line - message`

## 🚢 Déploiement sur Render

1. Créer un nouveau **Web Service** sur Render
2. Connecter votre repository Git
3. Configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Ajouter une **MySQL Database** depuis Render
5. Définir les variables d'environnement (voir `.env.example`)
6. Déployer!

## 🧪 Tests

```bash
# Tester le health check
curl http://localhost:8000/health

# Tester le scraping manuel
curl -X POST http://localhost:8000/scheduler/trigger/scrape_brvm

# Tester l'extraction PDF
curl -X POST http://localhost:8000/scheduler/trigger/extract_pdf_12h

# Récupérer les actions
curl http://localhost:8000/api/actions

# Récupérer le dernier indicateur
curl http://localhost:8000/api/indicateurs/latest
```

## 🛠️ Commandes utiles

```bash
# Docker Compose
docker-compose up -d                # Démarrer
docker-compose logs -f api          # Voir les logs
docker-compose ps                   # Statut des services
docker-compose restart api          # Redémarrer l'API
docker-compose down -v              # Arrêter et supprimer volumes

# Base de données
docker-compose exec mysql mysql -u root -p brvm_db  # Accéder à MySQL

# Maintenance
docker-compose exec api python -c "from app.database import init_db; init_db()"  # Réinitialiser DB
```

## 🐛 Dépannage

### Problème de connexion MySQL
```bash
# Vérifier que MySQL est démarré
docker-compose ps mysql

# Vérifier les logs MySQL
docker-compose logs mysql
```

### Erreur de scraping
```bash
# Vérifier les logs
tail -f logs/app.log

# Tester manuellement
curl https://www.brvm.org/fr/cours-actions/0
```

### PDF non téléchargé
```bash
# Vérifier l'URL du jour
python -c "from datetime import datetime; print(f'https://www.brvm.org/sites/default/files/boc_{datetime.now().strftime(\"%Y%m%d\")}_2.pdf')"

# Vérifier le dossier downloads
ls -la downloads/
```

## 📄 Licence

MIT License

## 👤 Auteur

BRVM Data API - 2025

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

---

**Note**: Cette API respecte les conditions d'utilisation du site BRVM. Utilisez-la de manière responsable.
