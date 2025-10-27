# app/api/routes/__init__.py
"""
Routes de l'API
"""
from . import actions, historique, indicateurs, webhooks, debug

__all__ = ['actions', 'historique', 'indicateurs', 'webhooks', 'debug']
