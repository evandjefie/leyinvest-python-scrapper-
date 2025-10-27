"""
Application FastAPI principale - BRVM Data API
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn

from app.config import settings
from app.database import init_db, check_db_connection
from app.utils.logger import app_logger
from app.services.scheduler import task_scheduler

# Import des routes
from app.api.routes import actions, historique, indicateurs, webhooks, debug


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application
    """
    # Démarrage
    app_logger.info("=" * 60)
    app_logger.info(f"🚀 Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    app_logger.info("=" * 60)

    try:
        # Vérifier la connexion à la base de données
        if not check_db_connection():
            app_logger.error("❌ Impossible de se connecter à la base de données")
            raise Exception("Connexion à la base de données échouée")

        # Initialiser les tables
        app_logger.info("📊 Initialisation de la base de données...")
        init_db()

        # Démarrer le planificateur de tâches
        app_logger.info("⏰ Démarrage du planificateur de tâches...")
        task_scheduler.start()

        app_logger.info("✅ Application démarrée avec succès")
        app_logger.info("=" * 60)

    except Exception as e:
        app_logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise

    yield  # L'application fonctionne ici

    # Arrêt
    app_logger.info("=" * 60)
    app_logger.info("🛑 Arrêt de l'application...")
    app_logger.info("=" * 60)

    try:
        # Arrêter le planificateur
        app_logger.info("⏰ Arrêt du planificateur de tâches...")
        task_scheduler.shutdown()
        app_logger.info("✅ Application arrêtée proprement")
    except Exception as e:
        app_logger.error(f"Erreur lors de l'arrêt: {e}")


# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware pour logger toutes les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware pour logger toutes les requêtes HTTP
    """
    start_time = datetime.now()

    # Log de la requête entrante
    app_logger.info(f"➡️  {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Calculer le temps de traitement
        process_time = (datetime.now() - start_time).total_seconds()

        # Log de la réponse
        app_logger.info(
            f"⬅️  {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        # Ajouter le temps de traitement dans les headers
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        app_logger.error(f"❌ Erreur lors du traitement de {request.method} {request.url.path}: {e}")
        raise


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire global des exceptions non gérées
    """
    app_logger.error(f"Exception non gérée: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Une erreur inattendue s'est produite",
            "timestamp": datetime.now().isoformat()
        }
    )


# Routes de base
@app.get(
    "/",
    tags=["Root"],
    summary="Page d'accueil de l'API",
    description="Informations de base sur l'API BRVM"
)
async def root():
    """
    Endpoint racine de l'API
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "documentation": "/docs",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Vérification de santé",
    description="Vérifie que l'API et la base de données sont opérationnelles"
)
async def health_check():
    """
    Endpoint de health check pour monitoring
    """
    db_status = check_db_connection()

    # Vérifier si le scheduler tourne
    scheduler_running = task_scheduler.scheduler.running

    overall_status = "healthy" if (db_status and scheduler_running) else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected" if db_status else "disconnected",
            "scheduler": "running" if scheduler_running else "stopped"
        },
        "version": settings.APP_VERSION
    }


@app.get(
    "/scheduler/status",
    tags=["Scheduler"],
    summary="Statut du planificateur",
    description="Récupère le statut et la liste des tâches planifiées"
)
async def scheduler_status():
    """
    Récupère les informations sur le planificateur et ses tâches
    """
    jobs = task_scheduler.scheduler.get_jobs()

    jobs_info = []
    for job in jobs:
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "scheduler_running": task_scheduler.scheduler.running,
        "jobs_count": len(jobs),
        "jobs": jobs_info,
        "timestamp": datetime.now().isoformat()
    }


@app.post(
    "/scheduler/trigger/{job_id}",
    tags=["Scheduler"],
    summary="Déclencher une tâche manuellement",
    description="Force l'exécution immédiate d'une tâche planifiée"
)
async def trigger_job(job_id: str):
    """
    Déclenche manuellement une tâche du scheduler

    **Paramètres:**
    - **job_id**: ID de la tâche (scrape_brvm, extract_pdf_12h, extract_pdf_18h)
    """
    valid_job_ids = ['scrape_brvm', 'extract_pdf_12h', 'extract_pdf_18h']

    if job_id not in valid_job_ids:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid job_id",
                "message": f"job_id doit être l'un de: {', '.join(valid_job_ids)}",
                "valid_ids": valid_job_ids
            }
        )

    try:
        task_scheduler.execute_now(job_id)
        return {
            "message": f"Tâche '{job_id}' programmée pour exécution immédiate",
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        app_logger.error(f"Erreur lors du déclenchement de la tâche {job_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Execution failed",
                "message": str(e)
            }
        )


# Inclusion des routes
app.include_router(actions.router)
app.include_router(historique.router)
app.include_router(indicateurs.router)
app.include_router(webhooks.router)
app.include_router(debug.router)  # Routes de débogage


# Point d'entrée pour exécution directe
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
