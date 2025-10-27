"""
Service d'extraction des indicateurs depuis les bulletins PDF BRVM
"""
import os
import re
import requests
from datetime import datetime, date, timedelta, time
from typing import Optional, Dict
from sqlalchemy.orm import Session
import pdfplumber
from app.config import settings
from app.models import IndicateurMarche
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFExtractor:
    """
    Extracteur d'indicateurs depuis les PDF du bulletin officiel BRVM
    """

    def __init__(self):
        self.downloads_dir = settings.DOWNLOADS_DIR
        os.makedirs(self.downloads_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Désactiver les warnings SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_pdf_date(self, reference_date: Optional[datetime] = None) -> date:
        """
        Détermine la date du PDF à télécharger selon les règles strictes :
        - Avant 17h30 → utiliser la veille
        - Samedi ou dimanche → utiliser le vendredi précédent
        - Le PDF n’existe que du lundi au vendredi

        Args:
            reference_date: Date/heure de référence (maintenant par défaut)

        Returns:
            Date du PDF à télécharger (toujours un lundi-vendredi)
        """
        if reference_date is None:
            reference_date = datetime.now()

        cutoff_time = time(17, 30, 0)
        current_date = reference_date.date()
        current_time = reference_date.time()

        # Étape 1 : Déterminer la date candidate selon l'heure
        if current_time < cutoff_time:
            candidate_date = current_date - timedelta(days=1)
        else:
            candidate_date = current_date

        # Étape 2 : Reculer jusqu'à un jour ouvré (lundi=0 à vendredi=4)
        while candidate_date.weekday() >= 5:  # 5=samedi, 6=dimanche
            candidate_date -= timedelta(days=1)

        logger.info(
            f"📅 Date cible calculée : {candidate_date} "
            f"(basée sur {reference_date.strftime('%Y-%m-%d %H:%M')})"
        )
        return candidate_date

    def generate_pdf_url(self, target_date: Optional[date] = None) -> tuple[str, str]:
        """
        Génère l'URL et le nom du fichier PDF pour une date donnée.

        Args:
            target_date: Date cible (utilise la logique métier si None)

        Returns:
            Tuple (URL du PDF, nom du fichier local)
        """
        if target_date is None:
            target_date = self.get_pdf_date()

        date_str = target_date.strftime('%Y%m%d')
        url = settings.BRVM_PDF_BASE_URL.format(date=date_str)
        filename = f"boc_{date_str}_2.pdf"

        logger.debug(f"URL générée: {url}")
        return url, filename

    def file_exists(self, filename: str) -> bool:
        """
        Vérifie si le fichier PDF existe déjà localement.

        Args:
            filename: Nom du fichier

        Returns:
            True si le fichier existe, False sinon
        """
        filepath = os.path.join(self.downloads_dir, filename)
        exists = os.path.exists(filepath)

        if exists:
            logger.info(f"Le fichier {filename} existe déjà localement")
        return exists

    def download_pdf(self, url: str, filename: str) -> Optional[str]:
        """
        Télécharge le PDF depuis l'URL.

        Args:
            url: URL du PDF
            filename: Nom du fichier à sauvegarder

        Returns:
            Chemin complet du fichier téléchargé ou None en cas d'erreur
        """
        filepath = os.path.join(self.downloads_dir, filename)

        try:
            logger.info(f"Téléchargement du PDF depuis: {url}")
            response = requests.get(
                url,
                headers=self.headers,
                timeout=60,
                stream=True,
                verify=False  # Désactive la vérification SSL
            )

            if response.status_code == 404:
                logger.error("Fichier non encore disponible (erreur 404)")
                return None

            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"PDF téléchargé avec succès: {filepath}")
            return filepath

        except requests.RequestException as e:
            logger.error(f"Erreur lors du téléchargement du PDF: {e}")
            return None

    def extract_indicators(self, pdf_path: str) -> Dict[str, Optional[float]]:
        """
        Extrait les 4 indicateurs clés depuis le PDF BRVM :
        - PER moyen du marché
        - Taux de rendement moyen du marché
        - Taux de rentabilité moyen du marché
        - Prime de risque du marché

        Args:
            pdf_path: Chemin vers le fichier PDF

        Returns:
            Dictionnaire avec les 4 indicateurs (float ou None)
        """
        indicators = {
            'taux_rendement_moyen': None,
            'per_moyen': None,
            'taux_rentabilite_moyen': None,
            'prime_risque_marche': None
        }

        try:
            logger.info(f"Extraction des indicateurs depuis: {pdf_path}")

            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += " " + text

            if not full_text.strip():
                logger.warning("Aucun texte extrait du PDF")
                return indicators

            # Nettoyer le texte : remplacer les sauts de ligne et espaces multiples par un seul espace
            cleaned_text = re.sub(r'\s+', ' ', full_text)

            # Patterns améliorés : supportent espaces, deux-points, tabulations, etc.
            patterns = {
                'per_moyen': r'PER\s+moyen\s+du\s+march[eé]\s*(?:\([^)]*\))?.{0,100}?([0-9]+[,.][0-9]+)',
                'taux_rendement_moyen': r'Taux\s+de\s+rendement\s+moyen\s+du\s+march[eé]\s*[:\s]*([0-9]+[,.][0-9]+)',
                'taux_rentabilite_moyen': r'Taux\s+de\s+rentabilit[ée]\s+moyen\s+du\s+march[eé]\s*[:\s]*([0-9]+[,.][0-9]+)',
                'prime_risque_marche': r'Prime\s+de\s+risque\s+du\s+march[eé]\s*[:\s]*([0-9]+[,.][0-9]+)'
            }

            for key, pattern in patterns.items():
                if indicators[key] is not None:
                    continue

                match = re.search(pattern, cleaned_text, re.IGNORECASE)
                if match:
                    try:
                        value_str = match.group(1).replace(',', '.')
                        indicators[key] = float(value_str)
                        logger.debug(f"✅ Trouvé {key}: {indicators[key]}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"⚠️ Impossible de convertir la valeur pour {key}: {match.group(1)} - {e}")

            found_count = sum(1 for v in indicators.values() if v is not None)
            logger.info(f"Extraction terminée: {found_count}/4 indicateurs trouvés")

            if found_count == 0:
                logger.warning("Aucun des 4 indicateurs clés n'a été trouvé dans le PDF")
                # Optionnel : loguer un extrait du texte pour debug
                preview = cleaned_text[:500].replace('\n', ' ')
                logger.debug(f"Extrait du PDF (500 premiers caractères): {preview}")

            return indicators

        except Exception as e:
            logger.error(f"❌ Erreur critique lors de l'extraction du PDF: {e}", exc_info=True)
            return indicators

    def save_to_database(self, indicators: Dict, pdf_url: str, target_date: date, db: Session) -> bool:
        """
        Sauvegarde ou met à jour les indicateurs dans la base de données.

        Args:
            indicators: Dictionnaire des indicateurs
            pdf_url: URL source du PDF
            target_date: Date du rapport
            db: Session SQLAlchemy

        Returns:
            True si succès, False sinon
        """
        try:
            existing = db.query(IndicateurMarche).filter(
                IndicateurMarche.date_rapport == target_date
            ).first()

            if existing:
                logger.info(f"Mise à jour des indicateurs pour {target_date}")
                existing.taux_rendement_moyen = indicators.get('taux_rendement_moyen')
                existing.per_moyen = indicators.get('per_moyen')
                existing.taux_rentabilite_moyen = indicators.get('taux_rentabilite_moyen')
                existing.prime_risque_marche = indicators.get('prime_risque_marche')
                existing.source_pdf = pdf_url
            else:
                logger.info(f"Insertion des indicateurs pour {target_date}")
                new_indicator = IndicateurMarche(
                    date_rapport=target_date,
                    taux_rendement_moyen=indicators.get('taux_rendement_moyen'),
                    per_moyen=indicators.get('per_moyen'),
                    taux_rentabilite_moyen=indicators.get('taux_rentabilite_moyen'),
                    prime_risque_marche=indicators.get('prime_risque_marche'),
                    source_pdf=pdf_url
                )
                db.add(new_indicator)

            db.commit()
            logger.info("Indicateurs sauvegardés avec succès en base de données")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en base: {e}")
            db.rollback()
            return False

    def cleanup_old_data(self, db: Session) -> int:
        """
        Supprime les indicateurs de marché plus anciens que DATA_RETENTION_DAYS.
        Conserve toujours les données des N derniers jours (inclus).

        Args:
            db: Session SQLAlchemy

        Returns:
            Nombre d'enregistrements supprimés
        """
        try:
            retention_days = settings.DATA_RETENTION_DAYS
            cutoff_date = datetime.now().date() - timedelta(days=retention_days)

            logger.debug(
                f"Nettoyage des données antérieures au {cutoff_date} "
                f"(conservation des {retention_days} derniers jours)"
            )

            deleted = db.query(IndicateurMarche).filter(
                IndicateurMarche.date_rapport < cutoff_date
            ).delete()

            db.commit()

            if deleted > 0:
                logger.info(
                    f"🧹 Nettoyage terminé : {deleted} enregistrement(s) supprimé(s) "
                    f"(plus vieux que {retention_days} jours)"
                )
            else:
                logger.debug("Aucune donnée obsolète à supprimer")

            return deleted

        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage des anciennes données: {e}")
            db.rollback()
            return 0

    def process_daily_pdf(self, db: Session, target_date: Optional[date] = None) -> bool:
        """
        Méthode principale : télécharge et traite le PDF quotidien.

        Args:
            db: Session SQLAlchemy
            target_date: Date cible (utilise la logique métier si None)

        Returns:
            True si succès, False sinon
        """
        logger.info("=== Démarrage du traitement du PDF quotidien ===")

        # Appliquer la logique métier si aucune date fournie
        if target_date is None:
            target_date = self.get_pdf_date()

        pdf_url, filename = self.generate_pdf_url(target_date)
        filepath = os.path.join(self.downloads_dir, filename)

        # Vérifier si le fichier existe déjà
        if not self.file_exists(filename):
            downloaded_path = self.download_pdf(pdf_url, filename)
            if not downloaded_path:
                logger.error("Échec du téléchargement du PDF")
                return False
        else:
            logger.info(f"Utilisation du fichier existant: {filename}")

        # Extraire les indicateurs
        indicators = self.extract_indicators(filepath)

        if all(v is None for v in indicators.values()):
            logger.warning("Aucun indicateur extrait, abandon de la sauvegarde")
            return False

        # Sauvegarder en base
        success = self.save_to_database(indicators, pdf_url, target_date, db)

        # Nettoyage quotidien avec rétention configurable
        self.cleanup_old_data(db)

        logger.info("=== Traitement du PDF terminé ===")
        return success
