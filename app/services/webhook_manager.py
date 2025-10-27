"""
Service de gestion et d'envoi des webhooks
"""
import requests
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.config import settings
from app.models import WebhookSubscription
from app.schemas import WebhookPayload
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class WebhookManager:
    """
    Gestionnaire pour l'envoi de notifications via webhooks
    """

    def __init__(self):
        self.timeout = settings.WEBHOOK_TIMEOUT
        self.max_retries = settings.WEBHOOK_MAX_RETRIES

    def get_active_webhooks(self, db: Session) -> List[WebhookSubscription]:
        """
        Récupère toutes les URLs de webhooks actives

        Args:
            db: Session SQLAlchemy

        Returns:
            Liste des webhooks actifs
        """
        try:
            webhooks = db.query(WebhookSubscription).filter(
                WebhookSubscription.is_active == 1
            ).all()

            logger.info(f"{len(webhooks)} webhook(s) actif(s) trouvé(s)")
            return webhooks

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des webhooks: {e}")
            return []

    def send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """
        Envoie une requête POST à une URL de webhook

        Args:
            url: URL du webhook
            payload: Données à envoyer

        Returns:
            True si succès, False sinon
        """
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'BRVM-API-Webhook/1.0'
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Envoi webhook vers {url} (tentative {attempt}/{self.max_retries})")

                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                response.raise_for_status()
                logger.info(f"Webhook envoyé avec succès à {url} (status: {response.status_code})")
                return True

            except requests.Timeout:
                logger.warning(f"Timeout lors de l'envoi à {url} (tentative {attempt})")
                if attempt == self.max_retries:
                    logger.error(f"Échec définitif après {self.max_retries} tentatives: {url}")
                    return False

            except requests.RequestException as e:
                logger.error(f"Erreur lors de l'envoi à {url}: {e}")
                if attempt == self.max_retries:
                    return False

            # Attendre avant de réessayer (backoff exponentiel)
            if attempt < self.max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Attente de {wait_time}s avant nouvelle tentative...")
                asyncio.sleep(wait_time)

        return False

    def broadcast_to_webhooks(self, payload: WebhookPayload, db: Session) -> Dict[str, int]:
        """
        Envoie le payload à tous les webhooks actifs

        Args:
            payload: Données à envoyer
            db: Session SQLAlchemy

        Returns:
            Statistiques d'envoi (success, failed)
        """
        stats = {'success': 0, 'failed': 0}

        webhooks = self.get_active_webhooks(db)

        if not webhooks:
            logger.info("Aucun webhook actif à notifier")
            return stats

        payload_dict = payload.model_dump(mode='json')

        logger.info(f"Diffusion vers {len(webhooks)} webhook(s)")

        for webhook in webhooks:
            success = self.send_webhook(webhook.url, payload_dict)

            if success:
                stats['success'] += 1
                # Mettre à jour la date de dernier déclenchement
                try:
                    webhook.last_triggered = datetime.now()
                    db.commit()
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour du webhook {webhook.id}: {e}")
            else:
                stats['failed'] += 1

        logger.info(f"Diffusion terminée: {stats['success']} succès, {stats['failed']} échecs")
        return stats

    def create_actions_payload(self, action_data: Dict[str, Any], event_type: str = "update") -> WebhookPayload:
        """
        Crée un payload pour les mises à jour d'actions

        Args:
            action_data: Données de l'action
            event_type: Type d'événement (insert, update)

        Returns:
            WebhookPayload formaté
        """
        return WebhookPayload(
            timestamp=datetime.now(),
            source="BRVM",
            type=event_type,
            data_type="actions",
            data=action_data
        )

    def create_indicators_payload(self, indicators_data: Dict[str, Any], event_type: str = "update") -> WebhookPayload:
        """
        Crée un payload pour les indicateurs de marché

        Args:
            indicators_data: Données des indicateurs
            event_type: Type d'événement (insert, update)

        Returns:
            WebhookPayload formaté
        """
        return WebhookPayload(
            timestamp=datetime.now(),
            source="BRVM",
            type=event_type,
            data_type="indicateurs_marche",
            data=indicators_data
        )

    def notify_actions_update(self, actions_count: int, db: Session) -> Dict[str, int]:
        """
        Notifie les webhooks d'une mise à jour des actions

        Args:
            actions_count: Nombre d'actions mises à jour
            db: Session SQLAlchemy

        Returns:
            Statistiques d'envoi
        """
        payload = self.create_actions_payload(
            {
                "message": f"{actions_count} actions mises à jour",
                "count": actions_count,
                "timestamp": datetime.now().isoformat()
            },
            event_type="bulk_update"
        )

        return self.broadcast_to_webhooks(payload, db)

    def notify_indicators_update(self, indicators: Dict[str, Any], db: Session) -> Dict[str, int]:
        """
        Notifie les webhooks d'une mise à jour des indicateurs

        Args:
            indicators: Dictionnaire des indicateurs
            db: Session SQLAlchemy

        Returns:
            Statistiques d'envoi
        """
        payload = self.create_indicators_payload(indicators, event_type="update")
        return self.broadcast_to_webhooks(payload, db)


# Instance globale
webhook_manager = WebhookManager()
