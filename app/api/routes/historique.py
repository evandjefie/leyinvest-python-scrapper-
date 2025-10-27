"""
Routes API pour l'historique des actions
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import HistoriqueAction
from app.schemas import HistoriqueResponse
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/historique", tags=["Historique"])


@router.get(
    "",
    response_model=List[HistoriqueResponse],
    summary="Historique des snapshots",
    description="Récupère l'historique des snapshots des actions avec filtres"
)
def get_historique(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    symbole: Optional[str] = Query(None, description="Filtrer par symbole"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Nombre de jours à récupérer"),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des snapshots avec filtrage

    **Paramètres:**
    - **skip**: Pagination - éléments à sauter
    - **limit**: Nombre maximum d'éléments
    - **symbole**: Filtrer par symbole spécifique
    - **days**: Limiter aux X derniers jours

    **Retour:**
    - Liste des snapshots historiques
    """
    try:
        query = db.query(HistoriqueAction)

        # Filtre par symbole
        if symbole:
            query = query.filter(HistoriqueAction.symbole == symbole.upper())

        # Filtre par période
        if days:
            date_limit = datetime.now() - timedelta(days=days)
            query = query.filter(HistoriqueAction.created_at >= date_limit)

        # Tri par date décroissante
        historique = query.order_by(HistoriqueAction.created_at.desc()).offset(skip).limit(limit).all()

        logger.info(f"Récupération de {len(historique)} snapshot(s) historique")
        return historique

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'historique")


@router.get(
    "/{symbole}",
    response_model=List[HistoriqueResponse],
    summary="Historique d'une action spécifique",
    description="Récupère tout l'historique d'une action par son symbole"
)
def get_historique_by_symbole(
    symbole: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique complet d'une action

    **Paramètres:**
    - **symbole**: Code symbole de l'action
    - **skip**: Pagination
    - **limit**: Nombre maximum d'éléments

    **Retour:**
    - Historique de l'action triée par date décroissante
    """
    try:
        historique = db.query(HistoriqueAction).filter(
            HistoriqueAction.symbole == symbole.upper()
        ).order_by(
            HistoriqueAction.created_at.desc()
        ).offset(skip).limit(limit).all()

        if not historique:
            logger.warning(f"Aucun historique trouvé pour: {symbole}")
            raise HTTPException(status_code=404, detail=f"Aucun historique pour l'action '{symbole}'")

        logger.info(f"Historique de {symbole}: {len(historique)} enregistrement(s)")
        return historique

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique de {symbole}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/{symbole}/latest",
    response_model=HistoriqueResponse,
    summary="Dernier snapshot d'une action",
    description="Récupère le snapshot le plus récent d'une action"
)
def get_latest_snapshot(
    symbole: str,
    db: Session = Depends(get_db)
):
    """
    Récupère le dernier snapshot d'une action

    **Paramètres:**
    - **symbole**: Code symbole de l'action

    **Retour:**
    - Snapshot le plus récent

    **Erreurs:**
    - 404: Aucun snapshot trouvé
    """
    try:
        snapshot = db.query(HistoriqueAction).filter(
            HistoriqueAction.symbole == symbole.upper()
        ).order_by(
            HistoriqueAction.created_at.desc()
        ).first()

        if not snapshot:
            logger.warning(f"Aucun snapshot trouvé pour: {symbole}")
            raise HTTPException(status_code=404, detail=f"Aucun snapshot pour '{symbole}'")

        logger.info(f"Dernier snapshot de {symbole} récupéré")
        return snapshot

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dernier snapshot de {symbole}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
