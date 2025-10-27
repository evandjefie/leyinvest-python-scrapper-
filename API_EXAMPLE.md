---

## 🔧 Routes de Débogage (Debug)

### 1. Scraper immédiatement
```http
POST /api/debug/scrape-now?send_webhook=true
```

**Description:** Lance le scraping des actions BRVM immédiatement sans attendre le scheduler

**Paramètres query:**
- `send_webhook` (optionnel): Envoyer les webhooks (défaut: true)

**Réponse:**
```json
{
  "success": true,
  "timestamp": "2025-10-25T10:30:00",
  "scraping_stats": {
    "inserted": 5,
    "updated": 40,
    "errors": 0
  },
  "webhooks": {
    "status": "queued",
    "message": "Webhooks en cours d'envoi"
  },
  "message": "5 action(s) insérée(s), 40 mise(s) à jour"
}
```

### 2. Extraire le PDF immédiatement
```http
POST /api/debug/extract-pdf-now?send_webhook=true
```

**Paramètres query:**
- `target_date` (optionnel): Date du PDF (YYYY-MM-DD). Si absent, utilise aujourd'hui
- `send_webhook` (optionnel): Envoyer les webhooks (défaut: true)

**Exemples:**
```bash
# PDF du jour
curl -X POST "http://localhost:8000/api/debug/extract-pdf-now"

# PDF d'une date spécifique
curl -X POST "http://localhost:8000/api/debug/extract-pdf-now?target_date=2025-10-22"
```

**Réponse:**
```json
{
  "success": true,
  "timestamp": "2025-10-25T12:05:00",
  "target_date": "2025-10-25",
  "pdf_url": "https://www.brvm.org/sites/default/files/boc_20251025_2.pdf",
  "filename": "boc_20251025_2.pdf",
  "indicators": {
    "taux_rendement_moyen": 7.36,
    "per_moyen": 12.78,
    "taux_rentabilite_moyen": 8.64,
    "prime_risque_marche": 2.11
  },
  "message": "Extraction réussie"
}
```

### 3. Tester le scraper (sans DB)
```http
GET /api/debug/test-scraper
```

**Description:** Teste le scraping sans écrire en base de données. Utile pour vérifier l'accessibilité du site BRVM.

**Réponse:**
```json
{
  "success": true,
  "timestamp": "2025-10-25T10:00:00",
  "url": "https://www.brvm.org/fr/cours-actions/0",
  "html_received": true,
  "html_size": 125847,
  "actions_found": 45,
  "sample_actions": [
    {
      "symbole": "BICC",
      "nom": "BICI Côte d'Ivoire",
      "volume": 15000,
      "cours_cloture": 7550.0,
      "variation": 0.67
    }
  ],
  "message": "45 actions trouvées et parsées avec succès"
}
```

### 4. Tester l'URL du PDF
```http
GET /api/debug/test-pdf-url?target_date=2025-10-25
```

**Description:** Vérifie si l'URL du PDF existe et est accessible

**Réponse:**
```json
{
  "success": true,
  "timestamp": "2025-10-25T10:00:00",
  "target_date": "2025-10-25",
  "pdf_url": "https://www.brvm.org/sites/default/files/boc_20251025_2.pdf",
  "filename": "boc_20251025_2.pdf",
  "status_code": 200,
  "accessible": true,
  "content_type": "application/pdf",
  "content_length": "245678",
  "message": "PDF accessible"
}
```

### 5. Statistiques de la base de données
```http
GET /api/debug/database-stats
```

**Description:** Affiche les statistiques actuelles de toutes les tables

**Réponse:**
```json
{
  "timestamp": "2025-10-25T10:00:00",
  "tables": {
    "actions": {
      "count": 45,
      "last_update": {
        "symbole": "BICC",
        "nom": "BICI Côte d'Ivoire",
        "updated_at": "2025-10-25T10:00:00"
      }
    },
    "historique_actions": {
      "count": 1250
    },
    "indicateurs_marche": {
      "count": 15,
      "last_entry": {
        "date_rapport": "2025-10-25",
        "created_at": "2025-10-25T12:05:00"
      }
    },
    "webhooks": {
      "total": 3,
      "active": 2,
      "inactive": 1
    }
  },
  "message": "Statistiques récupérées avec succès"
}
```

### 6. Diagnostic complet
```http
GET /api/debug/full-diagnostic
```

**Description:** Lance un diagnostic complet de tous les composants de l'application

**Réponse:**
```json
{
  "timestamp": "2025-10-25T10:00:00",
  "components": {
    "database": {
      "status": "✅ OK",
      "message": "Connexion réussie"
    },
    "scraper": {
      "status": "✅ OK",
      "message": "45 actions trouvées",
      "actions_count": 45
    },
    "pdf_url": {
      "status": "✅ OK",
      "message": "Code HTTP: 200",
      "url": "https://www.brvm# 📮 Collection de Requêtes API - BRVM Data API

## 🏠 Base URLs

- **Local**: `http://localhost:8000`
- **Production**: `https://votre-app.onrender.com`

---

## 🔍 Routes Système

### 1. Page d'accueil
```http
GET /
```

**Réponse:**
```json
{
  "name": "BRVM Data API",
  "version": "1.0.0",
  "description": "API officielle pour consulter les cours des actions BRVM",
  "documentation": "/docs",
  "status": "online",
  "timestamp": "2025-10-25T10:00:00"
}
```

### 2. Health Check
```http
GET /health
```

**Réponse:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-25T10:00:00",
  "components": {
    "database": "connected",
    "scheduler": "running"
  },
  "version": "1.0.0"
}
```

### 3. Statut du Scheduler
```http
GET /scheduler/status
```

**Réponse:**
```json
{
  "scheduler_running": true,
  "jobs_count": 3,
  "jobs": [
    {
      "id": "scrape_brvm",
      "name": "Scraping des cours BRVM",
      "next_run": "2025-10-25T10:30:00",
      "trigger": "interval[0:30:00]"
    },
    {
      "id": "extract_pdf_12h",
      "name": "Extraction PDF BRVM à 12h",
      "next_run": "2025-10-25T12:00:00",
      "trigger": "cron[hour='12', minute='0']"
    }
  ],
  "timestamp": "2025-10-25T10:00:00"
}
```

### 4. Déclencher une tâche manuellement
```http
POST /scheduler/trigger/scrape_brvm
```

**Job IDs disponibles:**
- `scrape_brvm` - Scraping des actions
- `extract_pdf_12h` - Extraction PDF 12h
- `extract_pdf_18h` - Extraction PDF 18h

---

## 📊 Routes Actions

### 1. Liste des actions (pagination)
```http
GET /api/actions?skip=0&limit=50
```

**Paramètres query:**
- `skip` (optionnel): Nombre d'éléments à sauter (défaut: 0)
- `limit` (optionnel): Nombre max d'éléments (défaut: 100, max: 1000)
- `symbole` (optionnel): Filtrer par symbole

**Réponse:**
```json
[
  {
    "id": 1,
    "symbole": "BICC",
    "nom": "BICI Côte d'Ivoire",
    "volume": 15000,
    "cours_veille": 7500.0,
    "cours_ouverture": 7520.0,
    "cours_cloture": 7550.0,
    "variation": 0.67,
    "updated_at": "2025-10-25T10:00:00"
  }
]
```

### 2. Filtrer par symbole
```http
GET /api/actions?symbole=BICC
```

### 3. Détails d'une action
```http
GET /api/actions/BICC
```

### 4. Top actions par volume
```http
GET /api/actions/top/volume?limit=10
```

**Paramètres:**
- `limit`: Nombre d'actions (défaut: 10, max: 50)

### 5. Top actions par variation
```http
GET /api/actions/top/variation?limit=10&ascending=false
```

**Paramètres:**
- `limit`: Nombre d'actions
- `ascending`: `false` pour hausses, `true` pour baisses

---

## 📜 Routes Historique

### 1. Historique complet
```http
GET /api/historique?skip=0&limit=100
```

**Paramètres query:**
- `skip`: Pagination
- `limit`: Limite
- `symbole` (optionnel): Filtrer par symbole
- `days` (optionnel): Limiter aux X derniers jours

**Réponse:**
```json
[
  {
    "id": 1,
    "symbole": "BICC",
    "data_snapshot": {
      "symbole": "BICC",
      "nom": "BICI Côte d'Ivoire",
      "volume": 15000,
      "cours_cloture": 7550.0,
      "variation": 0.67
    },
    "created_at": "2025-10-25T10:00:00"
  }
]
```

### 2. Historique d'une action
```http
GET /api/historique/BICC?limit=50
```

### 3. Historique des 7 derniers jours
```http
GET /api/historique?days=7
```

### 4. Dernier snapshot d'une action
```http
GET /api/historique/BICC/latest
```

---

## 📈 Routes Indicateurs

### 1. Liste des indicateurs
```http
GET /api/indicateurs?skip=0&limit=100
```

**Réponse:**
```json
[
  {
    "id": 1,
    "date_rapport": "2025-10-25",
    "taux_rendement_moyen": 7.36,
    "per_moyen": 12.78,
    "taux_rentabilite_moyen": 8.64,
    "prime_risque_marche": 2.11,
    "source_pdf": "https://www.brvm.org/sites/default/files/boc_20251025_2.pdf",
    "created_at": "2025-10-25T12:05:00"
  }
]
```

### 2. Dernier indicateur
```http
GET /api/indicateurs/latest
```

### 3. Indicateur par date
```http
GET /api/indicateurs/date/2025-10-25
```

### 4. Indicateurs sur une période
```http
GET /api/indicateurs/range?start_date=2025-10-01&end_date=2025-10-31
```

**Paramètres:**
- `start_date`: Date de début (YYYY-MM-DD)
- `end_date`: Date de fin (YYYY-MM-DD)

### 5. Résumé statistique du mois
```http
GET /api/indicateurs/stats/summary
```

**Réponse:**
```json
{
  "periode": "2025-10-01 à 2025-10-25",
  "count": 15,
  "moyennes": {
    "taux_rendement_moyen": 7.42,
    "per_moyen": 12.85,
    "taux_rentabilite_moyen": 8.68,
    "prime_risque_marche": 2.15
  }
}
```

---

## 🔔 Routes Webhooks

### 1. Enregistrer un webhook
```http
POST /api/webhooks/register
Content-Type: application/json

{
  "url": "https://webhook.site/unique-id",
  "description": "Webhook de test"
}
```

**Réponse:**
```json
{
  "id": 1,
  "url": "https://webhook.site/unique-id",
  "description": "Webhook de test",
  "is_active": true,
  "created_at": "2025-10-25T10:00:00",
  "last_triggered": null
}
```

### 2. Liste des webhooks
```http
GET /api/webhooks
```

**Paramètres query:**
- `active_only` (optionnel): `true` pour webhooks actifs seulement

### 3. Liste des webhooks actifs seulement
```http
GET /api/webhooks?active_only=true
```

### 4. Supprimer un webhook
```http
DELETE /api/webhooks/1
```

### 5. Activer/Désactiver un webhook
```http
PATCH /api/webhooks/1/toggle
```

### 6. Tester les webhooks
```http
POST /api/webhooks/test-push
```

**Réponse:**
```json
{
  "message": "Test envoyé à 3 webhook(s) actif(s)",
  "webhooks_count": 3
}
```

---

## 📤 Format du Payload Webhook

Tous les webhooks reçoivent un payload au format suivant:

### Pour les actions
```json
{
  "timestamp": "2025-10-25T10:00:00Z",
  "source": "BRVM",
  "type": "bulk_update",
  "data_type": "actions",
  "data": {
    "message": "45 actions mises à jour",
    "count": 45,
    "timestamp": "2025-10-25T10:00:00"
  }
}
```

### Pour les indicateurs
```json
{
  "timestamp": "2025-10-25T12:00:00Z",
  "source": "BRVM",
  "type": "update",
  "data_type": "indicateurs_marche",
  "data": {
    "date_rapport": "2025-10-25",
    "taux_rendement_moyen": 7.36,
    "per_moyen": 12.78,
    "taux_rentabilite_moyen": 8.64,
    "prime_risque_marche": 2.11
  }
}
```

---

## 🔧 Exemples avec cURL

### Actions
```bash
# Liste des actions
curl "http://localhost:8000/api/actions"

# Filtrer par symbole
curl "http://localhost:8000/api/actions?symbole=BICC"

# Top 10 volume
curl "http://localhost:8000/api/actions/top/volume?limit=10"
```

### Indicateurs
```bash
# Dernier indicateur
curl "http://localhost:8000/api/indicateurs/latest"

# Période
curl "http://localhost:8000/api/indicateurs/range?start_date=2025-10-01&end_date=2025-10-31"
```

### Webhooks
```bash
# Enregistrer
curl -X POST "http://localhost:8000/api/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/unique-id", "description": "Test"}'

# Tester
curl -X POST "http://localhost:8000/api/webhooks/test-push"
```

### Scheduler
```bash
# Déclencher scraping
curl -X POST "http://localhost:8000/scheduler/trigger/scrape_brvm"

# Déclencher extraction PDF
curl -X POST "http://localhost:8000/scheduler/trigger/extract_pdf_12h"
```

---

## 🐍 Exemples avec Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Récupérer les actions
response = requests.get(f"{BASE_URL}/api/actions")
actions = response.json()
print(f"Nombre d'actions: {len(actions)}")

# Dernier indicateur
response = requests.get(f"{BASE_URL}/api/indicateurs/latest")
indicateur = response.json()
print(f"PER moyen: {indicateur['per_moyen']}")

# Enregistrer un webhook
webhook_data = {
    "url": "https://your-domain.com/webhook",
    "description": "Python webhook"
}
response = requests.post(
    f"{BASE_URL}/api/webhooks/register",
    json=webhook_data
)
webhook = response.json()
print(f"Webhook ID: {webhook['id']}")
```

---

## 🟢 Exemples avec JavaScript/Node.js

```javascript
const BASE_URL = "http://localhost:8000";

// Récupérer les actions
fetch(`${BASE_URL}/api/actions`)
  .then(res => res.json())
  .then(data => console.log(`Actions: ${data.length}`));

// Dernier indicateur
fetch(`${BASE_URL}/api/indicateurs/latest`)
  .then(res => res.json())
  .then(data => console.log(`PER: ${data.per_moyen}`));

// Enregistrer un webhook
fetch(`${BASE_URL}/api/webhooks/register`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    url: "https://your-domain.com/webhook",
    description: "JS webhook"
  })
})
  .then(res => res.json())
  .then(data => console.log(`Webhook ID: ${data.id}`));
```

---

## 📝 Notes

- Toutes les dates sont au format ISO 8601
- Les timestamps incluent le fuseau horaire
- Les montants sont en FCFA
- Les variations sont en pourcentage
- La pagination par défaut est de 100 éléments max

---

**Pour plus d'informations, consultez la documentation Swagger: http://localhost:8000/docs**
