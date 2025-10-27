"""
Routes de débogage et de test pour développement
Ces routes permettent de tester le scraping et l'extraction sans attendre le scheduler
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, date
from app.database import get_db
from app.services.scraper import BRVMScraper
from app.services.pdf_extractor import PDFExtractor
from app.services.webhook_manager import webhook_manager
from app.utils.logger import setup_logger


logger = setup_logger(__name__)

router = APIRouter(prefix="/api/debug", tags=["Debug & Testing"])


@router.post(
    "/scrape-now",
    summary="🔥 Scraper les actions immédiatement",
    description="Lance le scraping des actions BRVM sans attendre le scheduler. Utile pour le développement et les tests."
)
def scrape_actions_now(
    background_tasks: BackgroundTasks,
    send_webhook: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Lance immédiatement le scraping des actions BRVM

    **Paramètres:**
    - **send_webhook**: Envoyer les notifications webhook (défaut: True)

    **Retour:**
    - Statistiques du scraping (insertions, mises à jour, erreurs)

    **Utilisation:**
    ```bash
    curl -X POST "http://localhost:8000/api/debug/scrape-now"
    ```
    """
    try:
        logger.info("🔥 Démarrage du scraping manuel via /debug/scrape-now")

        scraper = BRVMScraper()
        stats = scraper.scrape_and_save(db)

        # Envoyer les webhooks si demandé et si des données ont été modifiées
        webhook_stats = None
        if send_webhook and (stats['inserted'] > 0 or stats['updated'] > 0):
            total_count = stats['inserted'] + stats['updated']

            def send_webhooks_bg():
                webhook_stats = webhook_manager.notify_actions_update(total_count, db)
                logger.info(f"Webhooks envoyés: {webhook_stats}")

            background_tasks.add_task(send_webhooks_bg)
            webhook_stats = {"status": "queued", "message": "Webhooks en cours d'envoi"}

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "scraping_stats": stats,
            "webhooks": webhook_stats,
            "message": f"{stats['inserted']} action(s) insérée(s), {stats['updated']} mise(s) à jour"
        }

        logger.info(f"✅ Scraping manuel terminé: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors du scraping manuel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du scraping: {str(e)}"
        )


    """
    Lance immédiatement l'extraction du PDF des indicateurs en respectant les règles métier.

    **Paramètres:**
    - **target_date**: Date de référence (YYYY-MM-DD). Si None, utilise la date/heure actuelle.
      → La date réelle du PDF sera ajustée selon :
         - Avant 17h30 → veille
         - Samedi/dimanche → vendredi
    - **send_webhook**: Envoyer les notifications webhook (défaut: True)

    **Retour:**
    - Informations sur l'extraction et les indicateurs extraits

    **Exemples:**
    ```bash
    # PDF calculé automatiquement (selon heure actuelle)
    curl -X POST "http://localhost:8000/api/debug/extract-pdf-now"

    # PDF basé sur une date de référence (ex: simuler un lundi à 10h)
    curl -X POST "http://localhost:8000/api/debug/extract-pdf-now?target_date=2025-10-27"
    ```
    """
    try:
        # Étape 1 : Déterminer la référence temporelle
        if target_date is None:
            reference_datetime = datetime.now()
        else:
            # On simule "aujourd'hui à midi" pour appliquer les règles métier
            # (car on ne connaît pas l'heure voulue → on choisit une heure < 17h30)
            reference_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))

        logger.info(f"📄 Démarrage de l'extraction PDF manuel avec référence: {reference_datetime}")

        extractor = PDFExtractor()

        # Étape 2 : Appliquer les règles métier pour obtenir la vraie date du PDF
        actual_pdf_date = extractor.get_pdf_date(reference_datetime)
        pdf_url, filename = extractor.generate_pdf_url(actual_pdf_date)

        # Étape 3 : Traiter le PDF
        success = extractor.process_daily_pdf(db, actual_pdf_date)

        if not success:
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "reference_date": str(reference_datetime.date()),
                "computed_pdf_date": str(actual_pdf_date),
                "pdf_url": pdf_url,
                "message": "Échec de l'extraction. Vérifiez les logs pour plus de détails.",
                "hint": "Le PDF n'existe peut-être pas encore ou l'URL est incorrecte"
            }

        # Étape 4 : Récupérer les indicateurs
        from app.models import IndicateurMarche
        indicateur = db.query(IndicateurMarche).filter(
            IndicateurMarche.date_rapport == actual_pdf_date
        ).first()

        indicators_data = None
        if indicateur:
            indicators_data = {
                "taux_rendement_moyen": indicateur.taux_rendement_moyen,
                "per_moyen": indicateur.per_moyen,
                "taux_rentabilite_moyen": indicateur.taux_rentabilite_moyen,
                "prime_risque_marche": indicateur.prime_risque_marche
            }

            if send_webhook:
                def send_webhooks_bg():
                    webhook_stats = webhook_manager.notify_indicators_update(
                        {**indicators_data, "date_rapport": str(actual_pdf_date)},
                        db
                    )
                    logger.info(f"Webhooks envoyés: {webhook_stats}")

                background_tasks.add_task(send_webhooks_bg)

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "reference_date": str(reference_datetime.date()),
            "computed_pdf_date": str(actual_pdf_date),  # ← très utile pour le debug
            "pdf_url": pdf_url,
            "filename": filename,
            "indicators": indicators_data,
            "message": "Extraction réussie"
        }

        logger.info(f"✅ Extraction PDF manuelle terminée: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction PDF manuelle: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'extraction PDF: {str(e)}"
        )



@router.post(
    "/extract-pdf-now",
    summary="📄 Extraire le PDF immédiatement",
    description=(
        "Télécharge et extrait les indicateurs du PDF **en respectant les règles métier** :<br>"
        "- Avant 17h30 → PDF de la veille<br>"
        "- Samedi/dimanche → PDF du vendredi précédent<br>"
        "La date fournie (`target_date`) est utilisée comme **date de référence** (simulée à 12h00)."
    )
)
def extract_pdf_now(
    background_tasks: BackgroundTasks,
    target_date: Optional[date] = None,
    send_webhook: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Lance immédiatement l'extraction du PDF des indicateurs en appliquant les règles métier.

    **Paramètres:**
    - **target_date**: Date de référence (YYYY-MM-DD). Si None, utilise la date/heure actuelle.
      → Le système simule "12h00" de ce jour pour appliquer les règles (avant 17h30).
    - **send_webhook**: Envoyer les notifications webhook (défaut: True)

    **Retour:**
    - Informations sur l'extraction, avec distinction entre `reference_date` et `computed_pdf_date`

    **Exemples:**
    ```bash
    # PDF calculé automatiquement (selon l'heure actuelle)
    curl -X POST "http://localhost:8000/api/debug/extract-pdf-now"

    # Simuler l'extraction comme si on était le dimanche 26/10/2025
    curl -X POST "http://localhost:8000/api/debug/extract-pdf-now?target_date=2025-10-26"
    ```
    """
    try:
        extractor = PDFExtractor()

        # Étape 1 : Déterminer la date/heure de référence
        if target_date is None:
            reference_datetime = datetime.now()
        else:
            # Simuler 12h00 de la date donnée (toujours avant 17h30)
            reference_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))

        # Étape 2 : Appliquer les règles métier pour obtenir la vraie date du PDF
        actual_pdf_date = extractor.get_pdf_date(reference_datetime)

        logger.info(
            f"📄 Démarrage extraction PDF manuelle | "
            f"Référence: {reference_datetime.strftime('%Y-%m-%d %H:%M')} → "
            f"PDF cible: {actual_pdf_date}"
        )

        # Étape 3 : Générer l'URL et traiter
        pdf_url, filename = extractor.generate_pdf_url(actual_pdf_date)
        success = extractor.process_daily_pdf(db, actual_pdf_date)

        if not success:
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "reference_date": str(reference_datetime.date()),
                "computed_pdf_date": str(actual_pdf_date),
                "pdf_url": pdf_url,
                "message": "Échec de l'extraction. Vérifiez les logs pour plus de détails.",
                "hint": "Le PDF n'existe peut-être pas encore, ou une erreur réseau s'est produite."
            }

        # Étape 4 : Récupérer les indicateurs sauvegardés
        from app.models import IndicateurMarche
        indicateur = db.query(IndicateurMarche).filter(
            IndicateurMarche.date_rapport == actual_pdf_date
        ).first()

        indicators_data = None
        if indicateur:
            indicators_data = {
                "taux_rendement_moyen": indicateur.taux_rendement_moyen,
                "per_moyen": indicateur.per_moyen,
                "taux_rentabilite_moyen": indicateur.taux_rentabilite_moyen,
                "prime_risque_marche": indicateur.prime_risque_marche
            }

            if send_webhook:
                def send_webhooks_bg():
                    webhook_stats = webhook_manager.notify_indicators_update(
                        {**indicators_data, "date_rapport": str(actual_pdf_date)},
                        db
                    )
                    logger.info(f"Webhooks envoyés: {webhook_stats}")

                background_tasks.add_task(send_webhooks_bg)

        # Étape 5 : Retourner la réponse
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "reference_date": str(reference_datetime.date()),
            "computed_pdf_date": str(actual_pdf_date),
            "pdf_url": pdf_url,
            "filename": filename,
            "indicators": indicators_data,
            "message": "Extraction réussie"
        }

        logger.info(f"✅ Extraction PDF manuelle terminée: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'extraction PDF manuelle: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'extraction PDF: {str(e)}"
        )



@router.get(
    "/test-scraper",
    summary="🧪 Tester le scraper (sans DB)",
    description="Teste le scraping sans sauvegarder en base de données. Utile pour vérifier si le site est accessible."
)
def test_scraper() -> Dict[str, Any]:
    """
    Teste le scraper sans écrire en base de données

    **Retour:**
    - Test de connexion au site BRVM et parsing du HTML

    **Utilisation:**
    ```bash
    curl "http://localhost:8000/api/debug/test-scraper"
    ```
    """
    try:
        logger.info("🧪 Test du scraper (sans DB)")

        scraper = BRVMScraper()

        # Tester la récupération de la page
        html_content = scraper.fetch_page()

        if not html_content:
            return {
                "success": False,
                "message": "Impossible de récupérer la page BRVM",
                "url": scraper.url,
                "html_received": False
            }

        # Tester le parsing
        actions_data = scraper.parse_actions(html_content)

        # Prendre un échantillon de 3 actions
        sample_actions = actions_data[:3] if len(actions_data) > 3 else actions_data

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "url": scraper.url,
            "html_received": True,
            "html_size": len(html_content),
            "actions_found": len(actions_data),
            "sample_actions": sample_actions,
            "message": f"{len(actions_data)} actions trouvées et parsées avec succès"
        }

        logger.info(f"✅ Test scraper réussi: {len(actions_data)} actions")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors du test scraper: {e}", exc_info=True)
        return {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Erreur lors du test du scraper"
        }


@router.get(
    "/test-pdf-url",
    summary="🔗 Tester l'URL du PDF",
    description="Vérifie si l'URL du PDF du jour existe et est accessible"
)
def test_pdf_url(target_date: date = None) -> Dict[str, Any]:
    """
    Teste l'accessibilité de l'URL du PDF

    **Paramètres:**
    - **target_date**: Date du PDF (YYYY-MM-DD). Si None, utilise aujourd'hui

    **Retour:**
    - Statut de l'URL et informations sur le fichier

    **Utilisation:**
    ```bash
    curl "http://localhost:8000/api/debug/test-pdf-url"
    curl "http://localhost:8000/api/debug/test-pdf-url?target_date=2025-10-22"
    ```
    """
    try:
        if target_date is None:
            target_date = datetime.now().date()

        logger.info(f"🔗 Test de l'URL PDF pour {target_date}")

        extractor = PDFExtractor()
        pdf_url, filename = extractor.generate_pdf_url(target_date)

        # Tester l'URL avec une requête HEAD
        import requests
        response = requests.head(pdf_url, timeout=10, verify=False)

        is_accessible = response.status_code == 200

        result = {
            "success": is_accessible,
            "timestamp": datetime.now().isoformat(),
            "target_date": str(target_date),
            "pdf_url": pdf_url,
            "filename": filename,
            "status_code": response.status_code,
            "accessible": is_accessible,
            "content_type": response.headers.get('Content-Type', 'unknown'),
            "content_length": response.headers.get('Content-Length', 'unknown'),
            "message": "PDF accessible" if is_accessible else f"PDF non accessible (code {response.status_code})"
        }

        logger.info(f"✅ Test URL PDF: {result['message']}")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors du test URL PDF: {e}", exc_info=True)
        return {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "target_date": str(target_date) if target_date else "today",
            "error": str(e),
            "message": "Impossible de tester l'URL du PDF"
        }


@router.get(
    "/database-stats",
    summary="📊 Statistiques de la base de données",
    description="Affiche les statistiques actuelles de la base de données"
)
def database_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Récupère les statistiques de la base de données

    **Retour:**
    - Nombre d'enregistrements dans chaque table
    - Dernières mises à jour

    **Utilisation:**
    ```bash
    curl "http://localhost:8000/api/debug/database-stats"
    ```
    """
    try:
        from app.models import Action, HistoriqueAction, IndicateurMarche, WebhookSubscription

        # Compter les enregistrements
        actions_count = db.query(Action).count()
        historique_count = db.query(HistoriqueAction).count()
        indicateurs_count = db.query(IndicateurMarche).count()
        webhooks_count = db.query(WebhookSubscription).count()
        webhooks_active = db.query(WebhookSubscription).filter(WebhookSubscription.is_active == 1).count()

        # Dernière action mise à jour
        last_action = db.query(Action).order_by(Action.updated_at.desc()).first()
        last_action_data = None
        if last_action:
            last_action_data = {
                "symbole": last_action.symbole,
                "nom": last_action.nom,
                "updated_at": last_action.updated_at.isoformat()
            }

        # Dernier indicateur
        last_indicateur = db.query(IndicateurMarche).order_by(IndicateurMarche.date_rapport.desc()).first()
        last_indicateur_data = None
        if last_indicateur:
            last_indicateur_data = {
                "date_rapport": str(last_indicateur.date_rapport),
                "created_at": last_indicateur.created_at.isoformat()
            }

        result = {
            "timestamp": datetime.now().isoformat(),
            "tables": {
                "actions": {
                    "count": actions_count,
                    "last_update": last_action_data
                },
                "historique_actions": {
                    "count": historique_count
                },
                "indicateurs_marche": {
                    "count": indicateurs_count,
                    "last_entry": last_indicateur_data
                },
                "webhooks": {
                    "total": webhooks_count,
                    "active": webhooks_active,
                    "inactive": webhooks_count - webhooks_active
                }
            },
            "message": "Statistiques récupérées avec succès"
        }

        logger.info("✅ Statistiques DB récupérées")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des stats DB: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.post(
    "/clear-test-data",
    summary="🗑️ Nettoyer les données de test",
    description="Supprime toutes les données des tables (ATTENTION: destructif!)"
)
def clear_test_data(
    confirm: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Nettoie toutes les données des tables

    ⚠️ **ATTENTION**: Cette action est irréversible!

    **Paramètres:**
    - **confirm**: Doit être True pour confirmer la suppression

    **Utilisation:**
    ```bash
    curl -X POST "http://localhost:8000/api/debug/clear-test-data?confirm=true"
    ```
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Vous devez confirmer la suppression en passant confirm=true"
        )

    try:
        from app.models import Action, HistoriqueAction, IndicateurMarche, WebhookSubscription

        logger.warning("🗑️ Début de la suppression des données de test")

        # Compter avant suppression
        actions_before = db.query(Action).count()
        historique_before = db.query(HistoriqueAction).count()
        indicateurs_before = db.query(IndicateurMarche).count()
        webhooks_before = db.query(WebhookSubscription).count()

        # Supprimer
        db.query(HistoriqueAction).delete()
        db.query(Action).delete()
        db.query(IndicateurMarche).delete()
        db.query(WebhookSubscription).delete()

        db.commit()

        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "deleted": {
                "actions": actions_before,
                "historique": historique_before,
                "indicateurs": indicateurs_before,
                "webhooks": webhooks_before
            },
            "message": f"Suppression réussie: {actions_before + historique_before + indicateurs_before + webhooks_before} enregistrements supprimés"
        }

        logger.warning(f"✅ Données supprimées: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


@router.get(
    "/full-diagnostic",
    summary="🔍 Diagnostic complet",
    description="Lance un diagnostic complet de l'application (scraper, PDF, DB, webhooks)"
)
def full_diagnostic(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Effectue un diagnostic complet de l'application

    **Retour:**
    - État de tous les composants
    - Tests de connectivité
    - Statistiques

    **Utilisation:**
    ```bash
    curl "http://localhost:8000/api/debug/full-diagnostic"
    ```
    """
    diagnostic = {
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Test 1: Base de données
    try:
        from app.models import Action
        db.query(Action).first()
        diagnostic["components"]["database"] = {
            "status": "✅ OK",
            "message": "Connexion réussie"
        }
    except Exception as e:
        diagnostic["components"]["database"] = {
            "status": "❌ ERREUR",
            "message": str(e)
        }

    # Test 2: Scraper BRVM
    try:
        scraper = BRVMScraper()
        html = scraper.fetch_page()
        if html:
            actions = scraper.parse_actions(html)
            diagnostic["components"]["scraper"] = {
                "status": "✅ OK",
                "message": f"{len(actions)} actions trouvées",
                "actions_count": len(actions)
            }
        else:
            diagnostic["components"]["scraper"] = {
                "status": "⚠️ WARNING",
                "message": "Impossible de récupérer la page"
            }
    except Exception as e:
        diagnostic["components"]["scraper"] = {
            "status": "❌ ERREUR",
            "message": str(e)
        }

    # Test 3: URL PDF
    try:
        extractor = PDFExtractor()
        pdf_url, _ = extractor.generate_pdf_url()
        import requests
        response = requests.head(pdf_url, timeout=10)
        diagnostic["components"]["pdf_url"] = {
            "status": "✅ OK" if response.status_code == 200 else "⚠️ WARNING",
            "message": f"Code HTTP: {response.status_code}",
            "url": pdf_url
        }
    except Exception as e:
        diagnostic["components"]["pdf_url"] = {
            "status": "❌ ERREUR",
            "message": str(e)
        }

    # Test 4: Scheduler
    try:
        from app.services.scheduler import task_scheduler
        diagnostic["components"]["scheduler"] = {
            "status": "✅ OK" if task_scheduler.scheduler.running else "⚠️ STOPPED",
            "message": f"{len(task_scheduler.scheduler.get_jobs())} tâches actives",
            "running": task_scheduler.scheduler.running
        }
    except Exception as e:
        diagnostic["components"]["scheduler"] = {
            "status": "❌ ERREUR",
            "message": str(e)
        }

    # Test 5: Webhooks
    try:
        from app.models import WebhookSubscription
        webhooks_count = db.query(WebhookSubscription).filter(WebhookSubscription.is_active == 1).count()
        diagnostic["components"]["webhooks"] = {
            "status": "✅ OK",
            "message": f"{webhooks_count} webhook(s) actif(s)",
            "active_count": webhooks_count
        }
    except Exception as e:
        diagnostic["components"]["webhooks"] = {
            "status": "❌ ERREUR",
            "message": str(e)
        }

    # Résumé général
    all_ok = all(
        comp["status"].startswith("✅")
        for comp in diagnostic["components"].values()
    )

    diagnostic["overall_status"] = "✅ Tous les composants OK" if all_ok else "⚠️ Certains composants ont des problèmes"

    logger.info(f"🔍 Diagnostic complet effectué: {diagnostic['overall_status']}")
    return diagnostic
