#!/bin/bash

# Script de démarrage rapide pour BRVM Data API
# Ce script configure et lance l'application

set -e

echo "======================================"
echo "🚀 BRVM Data API - Démarrage"
echo "======================================"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si .env existe
if [ ! -f .env ]; then
    log_warn "Fichier .env non trouvé. Création à partir de .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        log_info "Fichier .env créé. Veuillez le configurer avant de continuer."
        exit 0
    else
        log_error ".env.example non trouvé!"
        exit 1
    fi
fi

# Créer les répertoires nécessaires
log_info "Création des répertoires..."
mkdir -p downloads logs

# Démarrer avec Docker Compose
if command -v docker-compose &> /dev/null; then
    log_info "Démarrage avec Docker Compose..."

    # Arrêter les conteneurs existants
    docker-compose down

    # Construire et démarrer
    docker-compose up --build -d

    log_info "Conteneurs démarrés!"
    log_info "Attente du démarrage complet (30 secondes)..."
    sleep 30

    # Vérifier le statut
    log_info "Statut des services:"
    docker-compose ps

    echo ""
    log_info "✅ Application démarrée avec succès!"
    echo ""
    echo "📝 Accès à l'application:"
    echo "   - API: http://localhost:8000"
    echo "   - Swagger UI: http://localhost:8000/docs"
    echo "   - ReDoc: http://localhost:8000/redoc"
    echo "   - Health Check: http://localhost:8000/health"
    echo ""
    echo "📊 Commandes utiles:"
    echo "   - Voir les logs: docker-compose logs -f api"
    echo "   - Arrêter: docker-compose down"
    echo "   - Redémarrer: docker-compose restart"
    echo ""

else
    log_warn "Docker Compose non trouvé. Installation locale..."

    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 n'est pas installé!"
        exit 1
    fi

    # Créer l'environnement virtuel si nécessaire
    if [ ! -d "venv" ]; then
        log_info "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi

    # Activer l'environnement virtuel
    log_info "Activation de l'environnement virtuel..."
    source venv/bin/activate

    # Installer les dépendances
    log_info "Installation des dépendances..."
    pip install -r requirements.txt

    # Lancer l'application
    log_info "Démarrage de l'application..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
