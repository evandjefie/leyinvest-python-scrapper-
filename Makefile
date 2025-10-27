.PHONY: help install dev build up down restart logs clean test

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose

help: ## Afficher l'aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installer les dépendances
	$(PIP) install -r requirements.txt

dev: ## Lancer en mode développement (local)
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build: ## Construire les images Docker
	$(DOCKER_COMPOSE) build

up: ## Démarrer les conteneurs Docker
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Application démarrée sur http://localhost:8000"
	@echo "📚 Documentation: http://localhost:8000/docs"

down: ## Arrêter les conteneurs Docker
	$(DOCKER_COMPOSE) down

restart: ## Redémarrer les conteneurs
	$(DOCKER_COMPOSE) restart

logs: ## Voir les logs
	$(DOCKER_COMPOSE) logs -f api

logs-all: ## Voir tous les logs
	$(DOCKER_COMPOSE) logs -f

ps: ## Statut des conteneurs
	$(DOCKER_COMPOSE) ps

shell: ## Ouvrir un shell dans le conteneur API
	$(DOCKER_COMPOSE) exec api /bin/bash

db-shell: ## Ouvrir un shell MySQL
	$(DOCKER_COMPOSE) exec mysql mysql -u root -p brvm_db

clean: ## Nettoyer les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

clean-all: clean down ## Nettoyage complet (avec volumes Docker)
	$(DOCKER_COMPOSE) down -v
	rm -rf downloads/*.pdf
	rm -rf logs/*.log

test: ## Lancer les tests
	pytest tests/ -v --cov=app --cov-report=html

test-api: ## Tester l'API en production
	@echo "🧪 Test de l'API..."
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@curl -s http://localhost:8000/ | python -m json.tool

trigger-scrape: ## Déclencher le scraping manuellement
	curl -X POST http://localhost:8000/scheduler/trigger/scrape_brvm

trigger-pdf: ## Déclencher l'extraction PDF manuellement
	curl -X POST http://localhost:8000/scheduler/trigger/extract_pdf_12h

init-db: ## Initialiser la base de données
	$(DOCKER_COMPOSE) exec api python -c "from app.database import init_db; init_db()"

backup-db: ## Sauvegarder la base de données
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec mysql mysqldump -u root -p brvm_db > backups/brvm_db_$(shell date +%Y%m%d_%H%M%S).sql

format: ## Formater le code avec black
	black app/ tests/

lint: ## Vérifier le code avec flake8
	flake8 app/ tests/ --max-line-length=120

setup: ## Configuration initiale du projet
	@echo "🔧 Configuration initiale..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ Fichier .env créé"; fi
	@mkdir -p downloads logs
	@echo "✅ Répertoires créés"
	@echo "⚠️  N'oubliez pas de configurer le fichier .env"

docker-rebuild: ## Reconstruire et redémarrer Docker
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d

stats: ## Afficher les statistiques du projet
	@echo "📊 Statistiques du projet:"
	@echo "  Lignes de code Python:"
	@find app/ -name "*.py" | xargs wc -l | tail -1
	@echo "  Nombre de fichiers:"
	@find app/ -name "*.py" | wc -l
	@echo "  Taille du projet:"
	@du -sh .
