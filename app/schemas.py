"""
Schémas Pydantic pour validation et sérialisation des données
"""
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime, date
from typing import Optional, Any, Dict


# ============ Schémas Actions ============

class ActionBase(BaseModel):
    """Schéma de base pour une action"""
    symbole: str = Field(..., max_length=10, description="Code symbole BRVM")
    nom: str = Field(..., max_length=255, description="Nom complet de l'action")
    volume: int = Field(default=0, ge=0, description="Volume échangé")
    cours_veille: Optional[float] = Field(None, description="Cours de la veille")
    cours_ouverture: Optional[float] = Field(None, description="Cours d'ouverture")
    cours_cloture: Optional[float] = Field(None, description="Cours de clôture")
    variation: Optional[float] = Field(None, description="Variation en pourcentage")


class ActionCreate(ActionBase):
    """Schéma pour créer une action"""
    pass


class ActionResponse(ActionBase):
    """Schéma de réponse pour une action"""
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Schémas Historique ============

class HistoriqueBase(BaseModel):
    """Schéma de base pour l'historique"""
    symbole: str = Field(..., max_length=10)
    data_snapshot: Dict[str, Any] = Field(..., description="Snapshot des données au format JSON")


class HistoriqueCreate(HistoriqueBase):
    """Schéma pour créer un historique"""
    pass


class HistoriqueResponse(HistoriqueBase):
    """Schéma de réponse pour l'historique"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Schémas Indicateurs ============

class IndicateurBase(BaseModel):
    """Schéma de base pour les indicateurs de marché"""
    date_rapport: date = Field(..., description="Date du rapport")
    taux_rendement_moyen: Optional[float] = Field(None, description="Taux de rendement moyen du marché")
    per_moyen: Optional[float] = Field(None, description="PER moyen du marché")
    taux_rentabilite_moyen: Optional[float] = Field(None, description="Taux de rentabilité moyen du marché")
    prime_risque_marche: Optional[float] = Field(None, description="Prime de risque du marché")
    source_pdf: Optional[str] = Field(None, max_length=255, description="URL du PDF source")


class IndicateurCreate(IndicateurBase):
    """Schéma pour créer un indicateur"""
    pass


class IndicateurResponse(IndicateurBase):
    """Schéma de réponse pour un indicateur"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Schémas Webhooks ============

class WebhookRegister(BaseModel):
    """Schéma pour enregistrer un webhook"""
    url: HttpUrl = Field(..., description="URL du webhook à notifier")
    description: Optional[str] = Field(None, max_length=255, description="Description du webhook")

    @validator('url')
    def validate_url(cls, v):
        url_str = str(v)
        if not (url_str.startswith('http://') or url_str.startswith('https://')):
            raise ValueError("L'URL doit commencer par http:// ou https://")
        return v


class WebhookResponse(BaseModel):
    """Schéma de réponse pour un webhook"""
    id: int
    url: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Schéma du payload envoyé aux webhooks"""
    timestamp: datetime = Field(default_factory=datetime.now, description="Date et heure de l'événement")
    source: str = Field(default="BRVM", description="Source des données")
    type: str = Field(..., description="Type d'événement (update, insert, etc.)")
    data_type: str = Field(..., description="Type de données (actions, indicateurs_marche)")
    data: Dict[str, Any] = Field(..., description="Données de l'événement")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-24T12:00:00Z",
                "source": "BRVM",
                "type": "update",
                "data_type": "indicateurs_marche",
                "data": {
                    "taux_rendement_moyen": 7.36,
                    "per_moyen": 12.78,
                    "taux_rentabilite_moyen": 8.64,
                    "prime_risque_marche": 2.11
                }
            }
        }


# ============ Schémas Génériques ============

class PaginationParams(BaseModel):
    """Paramètres de pagination"""
    skip: int = Field(default=0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(default=100, le=1000, description="Nombre maximum d'éléments à retourner")


class StatusResponse(BaseModel):
    """Schéma de réponse pour le statut de l'API"""
    status: str = Field(..., description="Statut de l'API")
    message: str = Field(..., description="Message détaillé")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(..., description="Version de l'API")


class ErrorResponse(BaseModel):
    """Schéma de réponse en cas d'erreur"""
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message d'erreur détaillé")
    timestamp: datetime = Field(default_factory=datetime.now)
