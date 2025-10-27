# 🚀 Guide de Démarrage Rapide - BRVM Data API

## ⚡ Démarrage en 5 minutes

### Option 1: Docker Compose (Recommandé)

```bash
# 1. Cloner et entrer dans le projet
git clone <votre-repo>
cd brvm-api

# 2. Configuration
cp .env.example .env
# Éditer .env si nécessaire

# 3. Démarrer
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/health
```

**C'est tout ! L'API est accessible sur http://localhost:8000/docs**

### Option 2: Local (Sans Docker)

```bash
# 1. Configuration
cp .env.example .env
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 2. Base de données (MySQL doit être installé)
mysql -u root -p < init.sql

# 3. Lancer
python -m uvicorn app.main:app --reload
```

## 📋 Checklist après installation

- [ ] L'API répond sur http://localhost:8000
- [ ] Swagger accessible sur http://localhost:8000/docs
- [ ] Health check OK: `curl http://localhost:8000/health`
- [ ] MySQL connecté (voir logs)
- [ ] Scheduler actif (voir `/scheduler/status`)

## 🎯 Premiers tests

### 1. Vérifier le statut
```bash
curl http://localhost:8000/health
```

### 2. Déclencher un scraping manuel
```bash
curl -X POST http://localhost:8000/scheduler/trigger/scrape_brvm
```

### 3. Récupérer les actions
```bash
curl http://localhost:8000/api/actions
```

### 4. Enregistrer un webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/unique-id", "description": "Test"}'
```

### 5. Tester les webhooks
```bash
curl -X POST http://localhost:8000/api/webhooks/test-push
```

## 📊 Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Endpoint principal |
| Swagger UI | http://localhost:8000/docs | Documentation interactive |
| ReDoc | http://localhost:8000/redoc | Documentation alternative |
| Health Check | http://localhost:8000/health | Statut de l'application |
| Scheduler | http://localhost:8000/scheduler/status | État des tâches |

## 🔧 Commandes utiles

### Avec Docker
```bash
# Voir les logs en temps réel
docker-compose logs -f api

# Redémarrer l'API
docker-compose restart api

# Arrêter tout
docker-compose down

# Arrêter et supprimer les données
docker-compose down -v
```

### Avec Makefile
```bash
make up          # Démarrer
make logs        # Voir les logs
make down        # Arrêter
make test        # Lancer les tests
make clean       # Nettoyer
```

## 🐛 Dépannage rapide

### L'API ne démarre pas
```bash
# Vérifier les logs
docker-compose logs api

# Vérifier MySQL
docker-compose logs mysql

# Redémarrer proprement
docker-compose down
docker-compose up -d
```

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL est démarré
docker-compose ps mysql

# Recréer la base
docker-compose down -v
docker-compose up -d
```

### Le scraping ne fonctionne pas
```bash
# Tester manuellement l'URL
curl https://www.brvm.org/fr/cours-actions/0

# Vérifier les logs du scraper
docker-compose logs api | grep scraping

# Déclencher manuellement
curl -X POST http://localhost:8000/scheduler/trigger/scrape_brvm
```

### PDF non téléchargé
```bash
# Vérifier l'URL du jour
date +%Y%m%d

# Tester manuellement
curl -I https://www.brvm.org/sites/default/files/boc_$(date +%Y%m%d)_2.pdf

# Déclencher manuellement
curl -X POST http://localhost:8000/scheduler/trigger/extract_pdf_12h
```

## 📝 Configuration importante

### Variables .env essentielles
```bash
# Base de données
DATABASE_URL=mysql+pymysql://brvm_user:brvm_password@localhost:3306/brvm_db

# Scraping
SCRAPER_INTERVAL_MINUTES=30

# Timezone (important pour le scheduler)
TIMEZONE=Africa/Abidjan
```

## 🎓 Exemples d'utilisation

### Récupérer toutes les actions
```bash
curl http://localhost:8000/api/actions
```

### Filtrer par symbole
```bash
curl "http://localhost:8000/api/actions?symbole=BICC"
```

### Top 10 actions par volume
```bash
curl "http://localhost:8000/api/actions/top/volume?limit=10"
```

### Dernier indicateur du marché
```bash
curl http://localhost:8000/api/indicateurs/latest
```

### Historique d'une action
```bash
curl http://localhost:8000/api/historique/BICC
```

### Indicateurs sur une période
```bash
curl "http://localhost:8000/api/indicateurs/range?start_date=2025-10-01&end_date=2025-10-31"
```

## 🔔 Configuration des Webhooks

### 1. Créer un webhook de test sur webhook.site
Allez sur https://webhook.site et copiez votre URL unique

### 2. Enregistrer le webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/VOTRE-ID-UNIQUE",
    "description": "Webhook de test"
  }'
```

### 3. Tester
```bash
curl -X POST http://localhost:8000/api/webhooks/test-push
```

Vérifiez sur webhook.site que vous avez reçu le payload !

## 📱 Intégration avec d'autres services

### Zapier
1. Créer un Zap avec "Webhooks by Zapier"
2. Copier l'URL du webhook
3. L'enregistrer dans l'API

### Make (Integromat)
1. Créer un scénario avec "Webhooks"
2. Copier l'URL du webhook
3. L'enregistrer dans l'API

### Discord
1. Créer un webhook Discord dans les paramètres du canal
2. Enregistrer l'URL dans l'API
3. Adapter le payload si nécessaire

## 🚀 Déploiement sur Render

### 1. Préparer le repository
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Sur Render
1. Créer un nouveau "Web Service"
2. Connecter votre repository GitHub
3. Configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
4. Ajouter une base MySQL depuis Render
5. Définir les variables d'environnement

### 3. Variables d'environnement Render
```
DATABASE_URL=<Render Database URL>
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=Africa/Abidjan
SCRAPER_INTERVAL_MINUTES=30
```

### 4. Tester
```bash
curl https://votre-app.onrender.com/health
```

## 📊 Monitoring et Maintenance

### Vérifier les logs
```bash
# Dernières 100 lignes
docker-compose logs --tail=100 api

# Suivre en temps réel
docker-compose logs -f api

# Filtrer par niveau
docker-compose logs api | grep ERROR
```

### Vérifier l'espace disque
```bash
# Voir les PDF téléchargés
ls -lh downloads/

# Voir les logs
ls -lh logs/

# Nettoyer les vieux PDF (garder 7 jours)
find downloads/ -name "*.pdf" -mtime +7 -delete
```

### Statistiques de la base
```bash
# Nombre d'actions
docker-compose exec mysql mysql -u root -p brvm_db -e "SELECT COUNT(*) FROM actions;"

# Nombre d'indicateurs
docker-compose exec mysql mysql -u root -p brvm_db -e "SELECT COUNT(*) FROM indicateurs_marche;"

# Taille de la base
docker-compose exec mysql mysql -u root -p brvm_db -e "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' FROM information_schema.TABLES WHERE table_schema = 'brvm_db';"
```

## 🔒 Sécurité

### Checklist de production
- [ ] Changer tous les mots de passe par défaut
- [ ] Utiliser HTTPS (certificat SSL)
- [ ] Limiter les origines CORS
- [ ] Activer l'authentification API (à implémenter)
- [ ] Restreindre l'accès à la base de données
- [ ] Surveiller les logs d'erreur
- [ ] Mettre en place des alertes

### Recommandations
1. **Ne jamais committer le fichier .env**
2. **Utiliser des secrets managers** (Render Secrets, AWS Secrets Manager)
3. **Limiter les webhooks** à des domaines de confiance
4. **Monitorer les requêtes** pour détecter les abus

## 📈 Optimisations

### Pour de meilleures performances

1. **Ajuster le pool de connexions**
```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

2. **Augmenter la fréquence de scraping**
```env
SCRAPER_INTERVAL_MINUTES=15
```

3. **Ajouter un cache Redis** (à implémenter)

4. **Utiliser Gunicorn** pour le mode production
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🎯 Prochaines étapes

1. ✅ Vérifier que tout fonctionne
2. 📝 Personnaliser les configurations
3. 🔔 Configurer vos webhooks
4. 🚀 Déployer en production
5. 📊 Monitorer les performances
6. 🔧 Ajuster selon vos besoins

## 💡 Astuces

### Utiliser httpie pour des requêtes plus lisibles
```bash
# Installer httpie
pip install httpie

# Utiliser
http GET http://localhost:8000/api/actions
http POST http://localhost:8000/api/webhooks/register url=https://example.com/webhook
```

### Créer des alias
```bash
# Ajouter dans ~/.bashrc ou ~/.zshrc
alias brvm-start='docker-compose up -d'
alias brvm-stop='docker-compose down'
alias brvm-logs='docker-compose logs -f api'
alias brvm-scrape='curl -X POST http://localhost:8000/scheduler/trigger/scrape_brvm'
```

### Surveiller en continu
```bash
# Installer watch
# Linux: apt-get install watch
# Mac: brew install watch

# Surveiller le health check
watch -n 5 'curl -s http://localhost:8000/health | python -m json.tool'
```

## 🆘 Support

### Problème non résolu ?
1. Vérifier les logs: `docker-compose logs api`
2. Vérifier le README.md complet
3. Consulter la documentation Swagger: http://localhost:8000/docs
4. Ouvrir une issue sur GitHub

### Ressources utiles
- Documentation FastAPI: https://fastapi.tiangolo.com
- Documentation SQLAlchemy: https://docs.sqlalchemy.org
- Documentation APScheduler: https://apscheduler.readthedocs.io
- Site BRVM: https://www.brvm.org

---

**🎉 Félicitations ! Votre API BRVM est opérationnelle !**

Pour toute question, consultez le README.md complet ou les logs de l'application.
