"""
Service de scraping des cours des actions BRVM
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.config import settings
from app.models import Action, HistoriqueAction
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BRVMScraper:
    """
    Scraper pour récupérer les cours des actions depuis le site BRVM
    """

    def __init__(self):
        self.url = settings.BRVM_ACTIONS_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Désactiver les warnings SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch_page(self) -> Optional[str]:
        """
        Récupère le contenu HTML de la page des cours

        Returns:
            Contenu HTML ou None en cas d'erreur
        """
        try:
            logger.info(f"Récupération de la page: {self.url}")
            # Désactiver la vérification SSL avec verify=False
            response = requests.get(
                self.url,
                headers=self.headers,
                timeout=30,
                verify=False  # Désactive la vérification SSL
            )
            response.raise_for_status()
            logger.info("Page récupérée avec succès")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération de la page: {e}")
            return None

    def parse_actions(self, html_content: str) -> List[Dict]:
        """
        Parse le HTML pour extraire les données des actions

        Args:
            html_content: Contenu HTML de la page

        Returns:
            Liste de dictionnaires contenant les données des actions
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            actions_data = []

            # IMPORTANT: Cibler la section spécifique contenant la table principale
            # Éviter les tables du sidebar (Top 5, Flop 5, etc.)
            main_section = soup.find('section', id='block-system-main')

            if not main_section:
                logger.warning("Section 'block-system-main' non trouvée")
                # Fallback: chercher dans toute la page
                main_section = soup
            else:
                logger.info("Section principale 'block-system-main' trouvée")

            # Chercher la table dans la section principale
            table = main_section.find('table', class_='table-striped')

            if not table:
                # Fallback: toute table dans la section
                table = main_section.find('table')

            if not table:
                logger.warning("Aucune table trouvée dans la section principale")
                return []

            logger.info(f"Table trouvée avec classes: {table.get('class', [])}")

            # Trouver toutes les lignes (avec ou sans tbody)
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                logger.info(f"Lignes trouvées dans tbody: {len(rows)}")
            else:
                # Prendre toutes les lignes sauf le header
                all_rows = table.find_all('tr')
                # Filtrer les lignes de header (celles avec des <th>)
                rows = [row for row in all_rows if not row.find('th')]
                logger.info(f"Lignes trouvées sans tbody (filtré header): {len(rows)}")

            if not rows:
                logger.warning("Aucune ligne de données trouvée")
                return []

            for idx, row in enumerate(rows, 1):
                cols = row.find_all('td')

                # Debug: afficher le nombre de colonnes des premières lignes
                if idx <= 3:
                    logger.info(f"Ligne {idx}: {len(cols)} colonnes - Symbole: {cols[0].get_text(strip=True) if cols else 'N/A'}")

                if len(cols) < 7:
                    logger.debug(f"Ligne {idx}: {len(cols)} colonnes (< 7), ignorée")
                    continue

                try:
                    # Fonction pour nettoyer et parser les nombres
                    def parse_float(value: str) -> Optional[float]:
                        """Parse un float en nettoyant les espaces et en remplaçant les virgules"""
                        try:
                            if not value or value.strip() in ['-', '0', '']:
                                return None
                            # Supprimer tous les espaces (y compris non-breaking spaces \xa0)
                            cleaned = value.replace(' ', '').replace(',', '.').replace('\xa0', '').replace('\u202f', '').strip()
                            return float(cleaned) if cleaned else None
                        except (ValueError, AttributeError) as e:
                            logger.debug(f"Erreur parse_float pour '{value}': {e}")
                            return None

                    def parse_int(value: str) -> int:
                        """Parse un entier en nettoyant les espaces"""
                        try:
                            if not value or value.strip() in ['-', '0', '']:
                                return 0
                            # Supprimer tous les espaces (y compris non-breaking spaces)
                            cleaned = value.replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
                            return int(cleaned) if cleaned else 0
                        except (ValueError, AttributeError) as e:
                            logger.debug(f"Erreur parse_int pour '{value}': {e}")
                            return 0

                    def parse_variation(td_element) -> Optional[float]:
                        """Parse la variation qui peut être dans un span"""
                        try:
                            # Chercher d'abord dans un span
                            span = td_element.find('span', class_=['text-good', 'text-bad', 'text-nul'])
                            if span:
                                text = span.get_text(strip=True)
                            else:
                                text = td_element.get_text(strip=True)

                            if not text or text == '-':
                                return None

                            # Nettoyer et convertir
                            cleaned = text.replace(' ', '').replace(',', '.').replace('\xa0', '').replace('\u202f', '').strip()
                            return float(cleaned) if cleaned else None
                        except (ValueError, AttributeError) as e:
                            logger.debug(f"Erreur parse_variation: {e}")
                            return None

                    # Extraction des données
                    symbole = cols[0].get_text(strip=True)
                    nom = cols[1].get_text(strip=True)

                    if not symbole:
                        logger.warning(f"Ligne {idx}: symbole vide, ignorée")
                        continue

                    action_dict = {
                        'symbole': symbole,
                        'nom': nom,
                        'volume': parse_int(cols[2].get_text(strip=True)),
                        'cours_veille': parse_float(cols[3].get_text(strip=True)),
                        'cours_ouverture': parse_float(cols[4].get_text(strip=True)),
                        'cours_cloture': parse_float(cols[5].get_text(strip=True)),
                        'variation': parse_variation(cols[6])
                    }

                    actions_data.append(action_dict)

                    if idx <= 3:  # Log les 3 premières pour debug
                        logger.info(f"✓ Action parsée: {symbole} - Vol: {action_dict['volume']}, Cours: {action_dict['cours_cloture']}, Var: {action_dict['variation']}%")

                except Exception as e:
                    logger.error(f"Erreur lors du parsing de la ligne {idx}: {e}", exc_info=True)
                    continue

            logger.info(f"🎉 {len(actions_data)} actions extraites avec succès")
            return actions_data

        except Exception as e:
            logger.error(f"Erreur lors du parsing du HTML: {e}", exc_info=True)
            return []

    def save_to_database(self, actions_data: List[Dict], db: Session) -> Dict[str, int]:
        """
        Sauvegarde ou met à jour les actions dans la base de données

        Args:
            actions_data: Liste des données d'actions
            db: Session SQLAlchemy

        Returns:
            Dictionnaire avec le nombre d'insertions et mises à jour
        """
        stats = {'inserted': 0, 'updated': 0, 'errors': 0}

        try:
            for action_data in actions_data:
                try:
                    symbole = action_data['symbole']

                    # Vérifier si l'action existe déjà
                    existing_action = db.query(Action).filter(Action.symbole == symbole).first()

                    if existing_action:
                        # Mise à jour
                        for key, value in action_data.items():
                            setattr(existing_action, key, value)
                        stats['updated'] += 1
                    else:
                        # Insertion
                        new_action = Action(**action_data)
                        db.add(new_action)
                        stats['inserted'] += 1

                    # Créer un snapshot dans l'historique
                    snapshot = HistoriqueAction(
                        symbole=symbole,
                        data_snapshot=action_data
                    )
                    db.add(snapshot)

                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde de {action_data.get('symbole')}: {e}")
                    stats['errors'] += 1
                    continue

            db.commit()
            logger.info(f"Base de données mise à jour: {stats}")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en base: {e}")
            db.rollback()
            raise

        return stats

    def scrape_and_save(self, db: Session) -> Dict[str, int]:
        """
        Méthode principale: scrape et sauvegarde en base

        Args:
            db: Session SQLAlchemy

        Returns:
            Statistiques de l'opération
        """
        logger.info("=== Démarrage du scraping BRVM ===")

        html_content = self.fetch_page()
        if not html_content:
            logger.error("Impossible de récupérer le contenu de la page")
            return {'inserted': 0, 'updated': 0, 'errors': 1}

        actions_data = self.parse_actions(html_content)
        if not actions_data:
            logger.warning("Aucune donnée d'action extraite")
            return {'inserted': 0, 'updated': 0, 'errors': 1}

        stats = self.save_to_database(actions_data, db)

        logger.info("=== Scraping BRVM terminé ===")
        return stats
