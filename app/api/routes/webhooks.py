"""
Routes API pour la gestion des webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import WebhookSubscription
from app.schemas import WebhookRegister, WebhookResponse, WebhookPayload
from app.services.webhook_manager import webhook_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post(
    "/register",
    response_model=WebhookResponse,
    status_code=201,
    summary="Enregistrer un webhook",
    description="Enregistre une nouvelle URL de webhook pour recevoir les notifications"
)
def register_webhook(
    webhook: WebhookRegister,
    db: Session = Depends(get_db)
):
    """
    Enregistre un nouveau webhook

    **Corps de la requête:**
    ```json
    {
        "url": "https://example.com/webhook",
        "description": "Mon webhook"
    }
    ```

    **Retour:**
    - Détails du webhook enregistré

    **Erreurs:**
    - 400: URL déjà enregistrée
    """
    try:
        # Vérifier si l'URL existe déjà
        existing = db.query(WebhookSubscription).filter(
            WebhookSubscription.url == str(webhook.url)
        ).first()

        if existing:
            logger.warning(f"Tentative d'enregistrement d'un webhook existant: {webhook.url}")
            raise HTTPException(
                status_code=400,
                detail="Cette URL de webhook est déjà enregistrée"
            )

        # Créer le nouveau webhook
        new_webhook = WebhookSubscription(
            url=str(webhook.url),
            description=webhook.description,
            is_active=1
        )

        db.add(new_webhook)
        db.commit()
        db.refresh(new_webhook)

        logger.info(f"Nouveau webhook enregistré: {webhook.url}")
        return new_webhook

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement")


@router.get(
    "",
    response_model=List[WebhookResponse],
    summary="Liste des webhooks",
    description="Récupère la liste de tous les webhooks enregistrés"
)
def list_webhooks(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Liste tous les webhooks

    **Paramètres:**
    - **active_only**: Si True, retourne uniquement les webhooks actifs

    **Retour:**
    - Liste des webhooks enregistrés
    """
    try:
        query = db.query(WebhookSubscription)

        if active_only:
            query = query.filter(WebhookSubscription.is_active == 1)

        webhooks = query.all()
        logger.info(f"Récupération de {len(webhooks)} webhook(s)")
        return webhooks

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des webhooks: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.delete(
    "/{webhook_id}",
    status_code=204,
    summary="Supprimer un webhook",
    description="Supprime un webhook enregistré"
)
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un webhook

    **Paramètres:**
    - **webhook_id**: ID du webhook à supprimer

    **Erreurs:**
    - 404: Webhook non trouvé
    """
    try:
        webhook = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == webhook_id
        ).first()

        if not webhook:
            logger.warning(f"Tentative de suppression d'un webhook inexistant: {webhook_id}")
            raise HTTPException(status_code=404, detail="Webhook non trouvé")

        db.delete(webhook)
        db.commit()

        logger.info(f"Webhook supprimé: {webhook_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du webhook {webhook_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.patch(
    "/{webhook_id}/toggle",
    response_model=WebhookResponse,
    summary="Activer/Désactiver un webhook",
    description="Active ou désactive un webhook sans le supprimer"
)
def toggle_webhook(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """
    Active ou désactive un webhook

    **Paramètres:**
    - **webhook_id**: ID du webhook

    **Retour:**
    - Webhook mis à jour

    **Erreurs:**
    - 404: Webhook non trouvé
    """
    try:
        webhook = db.query(WebhookSubscription).filter(
            WebhookSubscription.id == webhook_id
        ).first()

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook non trouvé")

        # Inverser le statut actif/inactif
        webhook.is_active = 1 if webhook.is_active == 0 else 0
        db.commit()
        db.refresh(webhook)

        status = "activé" if webhook.is_active == 1 else "désactivé"
        logger.info(f"Webhook {webhook_id} {status}")
        return webhook

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du toggle du webhook {webhook_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.post(
    "/test-push",
    summary="Tester les webhooks",
    description="Envoie un payload de test à tous les webhooks actifs"
)
def test_webhooks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Envoie un payload de test à tous les webhooks actifs

    **Retour:**
    - Message de confirmation
    """
    try:
        # Créer un payload de test
        test_payload = WebhookPayload(
            timestamp=datetime.now(),
            source="BRVM",
            type="test",
            data_type="test",
            data={
                "message": "Ceci est un test de webhook",
                "timestamp": datetime.now().isoformat()
            }
        )

        # Compter les webhooks actifs
        active_count = db.query(WebhookSubscription).filter(
            WebhookSubscription.is_active == 1
        ).count()

        if active_count == 0:
            logger.warning("Tentative d'envoi de test sans webhook actif")
            raise HTTPException(
                status_code=400,
                detail="Aucun webhook actif enregistré"
            )

        # Envoyer en arrière-plan
        def send_test():
            stats = webhook_manager.broadcast_to_webhooks(test_payload, db)
            logger.info(f"Test webhook terminé: {stats}")

        background_tasks.add_task(send_test)

        logger.info(f"Test de {active_count} webhook(s) lancé")
        return {
            "message": f"Test envoyé à {active_count} webhook(s) actif(s)",
            "webhooks_count": active_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du test des webhooks: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
