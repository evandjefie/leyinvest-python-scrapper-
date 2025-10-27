"""
Routes API pour les indicateurs du marché
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models import IndicateurMarche
from app.schemas import IndicateurResponse
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/indicateurs", tags=["Indicateurs"])


@router.get(
    "",
    response_model=List[IndicateurResponse],
    summary="Liste des indicateurs",
    description="Récupère la liste des indicateurs du marché avec pagination"
)
def get_indicateurs(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les indicateurs du marché

    **Paramètres:**
    - **skip**: Pagination - éléments à sauter
    - **limit**: Nombre maximum d'éléments

    **Retour:**
    - Liste des indicateurs triés par date décroissante
    """
    try:
        indicateurs = db.query(IndicateurMarche).order_by(
            IndicateurMarche.date_rapport.desc()
        ).offset(skip).limit(limit).all()

        logger.info(f"Récupération de {len(indicateurs)} indicateur(s)")
        return indicateurs

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des indicateurs: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des indicateurs")


@router.get(
    "/latest",
    response_model=IndicateurResponse,
    summary="Dernier indicateur",
    description="Récupère le dernier indicateur du marché disponible"
)
def get_latest_indicateur(db: Session = Depends(get_db)):
    """
    Récupère le dernier indicateur disponible

    **Retour:**
    - Indicateur le plus récent

    **Erreurs:**
    - 404: Aucun indicateur trouvé
    """
    try:
        indicateur = db.query(IndicateurMarche).order_by(
            IndicateurMarche.date_rapport.desc()
        ).first()

        if not indicateur:
            logger.warning("Aucun indicateur trouvé dans la base")
            raise HTTPException(status_code=404, detail="Aucun indicateur disponible")

        logger.info(f"Dernier indicateur récupéré: {indicateur.date_rapport}")
        return indicateur

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dernier indicateur: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/date/{date_rapport}",
    response_model=IndicateurResponse,
    summary="Indicateur par date",
    description="Récupère l'indicateur pour une date spécifique"
)
def get_indicateur_by_date(
    date_rapport: date,
    db: Session = Depends(get_db)
):
    """
    Récupère l'indicateur pour une date précise

    **Paramètres:**
    - **date_rapport**: Date au format YYYY-MM-DD

    **Retour:**
    - Indicateur de la date spécifiée

    **Erreurs:**
    - 404: Aucun indicateur pour cette date
    """
    try:
        indicateur = db.query(IndicateurMarche).filter(
            IndicateurMarche.date_rapport == date_rapport
        ).first()

        if not indicateur:
            logger.warning(f"Aucun indicateur trouvé pour la date: {date_rapport}")
            raise HTTPException(
                status_code=404,
                detail=f"Aucun indicateur pour la date {date_rapport}"
            )

        logger.info(f"Indicateur du {date_rapport} récupéré")
        return indicateur

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'indicateur du {date_rapport}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/range",
    response_model=List[IndicateurResponse],
    summary="Indicateurs sur une période",
    description="Récupère les indicateurs entre deux dates"
)
def get_indicateurs_range(
    start_date: date = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Récupère les indicateurs sur une période

    **Paramètres:**
    - **start_date**: Date de début
    - **end_date**: Date de fin

    **Retour:**
    - Liste des indicateurs dans la période
    """
    try:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="La date de début doit être antérieure à la date de fin"
            )

        indicateurs = db.query(IndicateurMarche).filter(
            IndicateurMarche.date_rapport >= start_date,
            IndicateurMarche.date_rapport <= end_date
        ).order_by(IndicateurMarche.date_rapport.desc()).all()

        logger.info(f"Récupération de {len(indicateurs)} indicateur(s) entre {start_date} et {end_date}")
        return indicateurs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des indicateurs sur période: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get(
    "/stats/summary",
    summary="Résumé statistique",
    description="Résumé statistique des indicateurs du mois en cours"
)
def get_indicators_summary(db: Session = Depends(get_db)):
    """
    Résumé statistique des indicateurs

    **Retour:**
    - Statistiques agrégées du mois en cours
    """
    try:
        # Premier jour du mois en cours
        today = datetime.now().date()
        first_day = date(today.year, today.month, 1)

        indicateurs = db.query(IndicateurMarche).filter(
            IndicateurMarche.date_rapport >= first_day
        ).all()

        if not indicateurs:
            return {
                "periode": f"{first_day} à {today}",
                "count": 0,
                "message": "Aucune donnée pour le mois en cours"
            }

        # Calcul des moyennes
        avg_taux_rendement = sum(i.taux_rendement_moyen for i in indicateurs if i.taux_rendement_moyen) / len([i for i in indicateurs if i.taux_rendement_moyen]) if any(i.taux_rendement_moyen for i in indicateurs) else None
        avg_per = sum(i.per_moyen for i in indicateurs if i.per_moyen) / len([i for i in indicateurs if i.per_moyen]) if any(i.per_moyen for i in indicateurs) else None
        avg_rentabilite = sum(i.taux_rentabilite_moyen for i in indicateurs if i.taux_rentabilite_moyen) / len([i for i in indicateurs if i.taux_rentabilite_moyen]) if any(i.taux_rentabilite_moyen for i in indicateurs) else None
        avg_prime_risque = sum(i.prime_risque_marche for i in indicateurs if i.prime_risque_marche) / len([i for i in indicateurs if i.prime_risque_marche]) if any(i.prime_risque_marche for i in indicateurs) else None

        summary = {
            "periode": f"{first_day} à {today}",
            "count": len(indicateurs),
            "moyennes": {
                "taux_rendement_moyen": round(avg_taux_rendement, 2) if avg_taux_rendement else None,
                "per_moyen": round(avg_per, 2) if avg_per else None,
                "taux_rentabilite_moyen": round(avg_rentabilite, 2) if avg_rentabilite else None,
                "prime_risque_marche": round(avg_prime_risque, 2) if avg_prime_risque else None
            }
        }

        logger.info(f"Résumé statistique calculé pour {len(indicateurs)} indicateur(s)")
        return summary

    except Exception as e:
        logger.error(f"Erreur lors du calcul du résumé: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
