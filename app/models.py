"""
Modèles SQLAlchemy pour les tables de la base de données
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


class Action(Base):
    """
    Modèle pour la table des actions BRVM
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbole = Column(String(10), unique=True, nullable=False, index=True)
    nom = Column(String(255), nullable=False)
    volume = Column(Integer, default=0)
    cours_veille = Column(Float, nullable=True)
    cours_ouverture = Column(Float, nullable=True)
    cours_cloture = Column(Float, nullable=True)
    variation = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Action {self.symbole} - {self.nom}>"


class HistoriqueAction(Base):
    """
    Modèle pour l'historique des snapshots des actions
    """
    __tablename__ = "historique_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbole = Column(String(10), nullable=False, index=True)
    data_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Index composé pour optimiser les requêtes par symbole et date
    __table_args__ = (
        Index('idx_symbole_date', 'symbole', 'created_at'),
    )

    def __repr__(self):
        return f"<HistoriqueAction {self.symbole} - {self.created_at}>"


class IndicateurMarche(Base):
    """
    Modèle pour les indicateurs du marché extraits des PDF
    """
    __tablename__ = "indicateurs_marche"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_rapport = Column(Date, unique=True, nullable=False, index=True)
    taux_rendement_moyen = Column(Float, nullable=True)
    per_moyen = Column(Float, nullable=True)
    taux_rentabilite_moyen = Column(Float, nullable=True)
    prime_risque_marche = Column(Float, nullable=True)
    source_pdf = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<IndicateurMarche {self.date_rapport}>"


class WebhookSubscription(Base):
    """
    Modèle pour les URLs de webhooks enregistrées
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(512), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)  # 1=actif, 0=inactif
    created_at = Column(DateTime, default=func.now())
    last_triggered = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<WebhookSubscription {self.url}>"
