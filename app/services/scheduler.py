"""
Service de planification des tâches automatiques avec APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from app.config import settings
from app.database import get_db_context
from app.services.scraper import BRVMScraper
from app.services.pdf_extractor import PDFExtractor
from app.services.webhook_manager import webhook_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskScheduler:
    """
    Gestionnaire de tâches planifiées pour l'application BRVM
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
        self.scraper = BRVMScraper()
        self.pdf_extractor = PDFExtractor()

    def scrape_brvm_task(self):
        """
        Tâche de scraping des actions BRVM
        """
        try:
            logger.info("🔄 Exécution de la tâche de scraping BRVM")

            with get_db_context() as db:
                stats = self.scraper.scrape_and_save(db)

                # Notifier les webhooks si des données ont été mises à jour
                if stats['inserted'] > 0 or stats['updated'] > 0:
                    total_count = stats['inserted'] + stats['updated']
                    webhook_stats = webhook_manager.notify_actions_update(total_count, db)
                    logger.info(f"Webhooks notifiés: {webhook_stats}")

                logger.info(f"✅ Scraping terminé: {stats}")

        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping BRVM: {e}", exc_info=True)

    def extract_pdf_task(self):
        """
        Tâche d'extraction du PDF quotidien
        """
        try:
            logger.info("📄 Exécution de la tâche d'extraction PDF")

            with get_db_context() as db:
                success = self.pdf_extractor.process_daily_pdf(db)

                if success:
                    # Récupérer les derniers indicateurs pour notification
                    from app.models import IndicateurMarche
                    latest = db.query(IndicateurMarche).order_by(
                        IndicateurMarche.date_rapport.desc()
                    ).first()

                    if latest:
                        indicators_data = {
                            'date_rapport': latest.date_rapport.isoformat(),
                            'taux_rendement_moyen': latest.taux_rendement_moyen,
                            'per_moyen': latest.per_moyen,
                            'taux_rentabilite_moyen': latest.taux_rentabilite_moyen,
                            'prime_risque_marche': latest.prime_risque_marche
                        }

                        webhook_stats = webhook_manager.notify_indicators_update(indicators_data, db)
                        logger.info(f"Webhooks notifiés: {webhook_stats}")

                    logger.info("✅ Extraction PDF terminée avec succès")
                else:
                    logger.warning("⚠️ Extraction PDF terminée sans données")

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'extraction PDF: {e}", exc_info=True)

    def setup_jobs(self):
        """
        Configure toutes les tâches planifiées
        """
        # Tâche 1: Scraping BRVM toutes les 30 minutes
        self.scheduler.add_job(
            self.scrape_brvm_task,
            trigger=IntervalTrigger(minutes=settings.SCRAPER_INTERVAL_MINUTES),
            id='scrape_brvm',
            name='Scraping des cours BRVM',
            replace_existing=True,
            max_instances=1,  # Éviter les exécutions simultanées
            coalesce=True     # Fusionner les exécutions manquées
        )
        logger.info(f"✓ Tâche de scraping planifiée: toutes les {settings.SCRAPER_INTERVAL_MINUTES} minutes")

        # Tâche 2: Extraction PDF quotidienne à 12h et 18h
        for hour in settings.PDF_DOWNLOAD_HOURS:
            self.scheduler.add_job(
                self.extract_pdf_task,
                trigger=CronTrigger(hour=hour, minute=0, timezone=settings.TIMEZONE),
                id=f'extract_pdf_{hour}h',
                name=f'Extraction PDF BRVM à {hour}h',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            logger.info(f"✓ Tâche d'extraction PDF planifiée: chaque jour à {hour}:00")

        logger.info("✅ Toutes les tâches planifiées ont été configurées")

    def start(self):
        """
        Démarre le planificateur
        """
        try:
            self.setup_jobs()
            self.scheduler.start()
            logger.info("🚀 Planificateur de tâches démarré")

            # Afficher les tâches planifiées
            jobs = self.scheduler.get_jobs()
            logger.info(f"📋 {len(jobs)} tâche(s) active(s):")
            for job in jobs:
                logger.info(f"   - {job.name} (ID: {job.id}, Prochaine exécution: {job.next_run_time})")

        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du planificateur: {e}")
            raise

    def shutdown(self):
        """
        Arrête proprement le planificateur
        """
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("🛑 Planificateur de tâches arrêté")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du planificateur: {e}")

    def execute_now(self, job_id: str):
        """
        Exécute immédiatement une tâche planifiée

        Args:
            job_id: ID de la tâche à exécuter
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"⚡ Tâche '{job_id}' programmée pour exécution immédiate")
            else:
                logger.warning(f"Tâche '{job_id}' introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la tâche '{job_id}': {e}")


# Instance globale du planificateur
task_scheduler = TaskScheduler()
