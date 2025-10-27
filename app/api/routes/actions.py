"""
Routes API pour les actions BRVM
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Action
from app.schemas import ActionResponse, PaginationParams
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/actions", tags=["Actions"])


@router.get(
    "",
    response_model=List[ActionResponse],
    summary="Liste des actions",
    description="Récupère la liste des actions BRVM avec pagination et filtrage optionnel par symbole"
)
def get_actions(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    symbole: Optional[str] = Query(None, description="Filtrer par symbole (ex: BICC)"),
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les actions avec pagination optionnelle et filtre par symbole

    **Paramètres:**
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre maximum d'éléments à retourner
    - **symbole**: Filtrer par symbole spécifique (optionnel)

    **Retour:**
    - Liste des actions correspondant aux critères
    """
    try:
        query = db.query(Action)

        # Filtrage par symbole si spécifié
        if symbole:
            query = query.filter(Action.symbole.ilike(f"%{symbole}%"))

        # Pagination
        actions = query.offset(skip).limit(limit).all()

        logger.info(f"Récupération de {len(actions)} action(s)")
        return actions

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des actions: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des actions")


@router.get(
    "/{symbole}",
    response_model=ActionResponse,
    summary="Détails d'une action",
    description="Récupère les détails complets d'une action spécifique par son symbole"
)
def get_action_by_symbole(
    symbole: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'une action spécifique

    **Paramètres:**
    - **symbole**: Code symbole de l'action (ex: BICC, ETIT, SDCC)

    **Retour:**
    - Détails complets de l'action

    **Erreurs:**
    - 404: Action non trouvée
    """
    try:
        action = db.query(Action).filter(Action.symbole == symbole.upper()).first()

        if not action:
            logger.warning(f"Action non trouvée: {symbole}")
            raise HTTPException(status_code=404, detail=f"Action '{symbole}' non trouvée")

        logger.info(f"Action trouvée: {symbole}")
        return action

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'action {symbole}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/top/volume",
    response_model=List[ActionResponse],
    summary="Top actions par volume",
    description="Récupère les actions avec le plus grand volume échangé"
)
def get_top_by_volume(
    limit: int = Query(10, ge=1, le=50, description="Nombre d'actions à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupère les actions classées par volume décroissant

    **Paramètres:**
    - **limit**: Nombre d'actions à retourner (max 50)

    **Retour:**
    - Liste des actions triées par volume décroissant
    """
    try:
        actions = db.query(Action).order_by(Action.volume.desc()).limit(limit).all()
        logger.info(f"Top {len(actions)} actions par volume récupérées")
        return actions
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du top volume: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/top/variation",
    response_model=List[ActionResponse],
    summary="Top actions par variation",
    description="Récupère les actions avec la plus forte variation (positive ou négative)"
)
def get_top_by_variation(
    limit: int = Query(10, ge=1, le=50, description="Nombre d'actions à retourner"),
    ascending: bool = Query(False, description="True pour variations négatives, False pour positives"),
    db: Session = Depends(get_db)
):
    """
    Récupère les actions classées par variation

    **Paramètres:**
    - **limit**: Nombre d'actions à retourner
    - **ascending**: False pour plus fortes hausses, True pour plus fortes baisses

    **Retour:**
    - Liste des actions triées par variation
    """
    try:
        if ascending:
            actions = db.query(Action).filter(Action.variation.isnot(None)).order_by(Action.variation.asc()).limit(limit).all()
        else:
            actions = db.query(Action).filter(Action.variation.isnot(None)).order_by(Action.variation.desc()).limit(limit).all()

        logger.info(f"Top {len(actions)} actions par variation récupérées")
        return actions
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du top variation: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
