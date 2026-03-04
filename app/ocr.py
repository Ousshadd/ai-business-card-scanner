import pytesseract
import re
import logging

logger = logging.getLogger(__name__)

class OCREngine:
    """Moteur OCR utilisant Tesseract"""
    
    def __init__(self):
        # Configuration pour Windows (décommente si besoin)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Langues supportées (français + anglais)
        self.langs = 'fra+eng'
        
        # Différentes configurations de segmentation
        self.psm_configs = [
            '--oem 3 --psm 6',      # Bloc de texte uniforme
            '--oem 3 --psm 4',      # Texte sur une colonne
            '--oem 3 --psm 3',      # Détection automatique
            '--oem 3 --psm 1',      # Détection avec orientation
        ]
        
    def extract_text(self, image):
        """
        Extrait le texte d'une image prétraitée
        
        Args:
            image: image numpy array prétraitée
            
        Returns:
            texte extrait et nettoyé
        """
        try:
            all_texts = []
            
            # Essayer différentes configurations
            for config in self.psm_configs:
                text = pytesseract.image_to_string(
                    image,
                    lang=self.langs,
                    config=config
                )
                if text and len(text.strip()) > 10:  # Garder si texte significatif
                    all_texts.append(text)
                    logger.info(f"Configuration {config}: {len(text)} caractères")
            
            # Prendre le texte le plus long (souvent le meilleur)
            if all_texts:
                best_text = max(all_texts, key=len)
            else:
                # Fallback: essayer sans configuration spécifique
                best_text = pytesseract.image_to_string(image, lang=self.langs)
            
            # Nettoyer le texte
            cleaned_text = self._clean_text(best_text)
            
            logger.info(f"OCR terminé: {len(cleaned_text)} caractères")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Erreur OCR: {str(e)}")
            return ""
    
    def _clean_text(self, text):
        """Nettoie le texte extrait"""
        if not text:
            return ""
        
        # Enlever les lignes vides
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Nettoyer chaque ligne
        cleaned_lines = []
        for line in lines:
            # Garder lettres, chiffres, @, ., espace, tirets, parenthèses, +
            clean_line = re.sub(r'[^\w\s@\.\-+\(\)]', '', line)
            # Enlever les espaces multiples
            clean_line = re.sub(r'\s+', ' ', clean_line)
            if clean_line and len(clean_line) > 1:  # Ignorer trop courts
                cleaned_lines.append(clean_line)
        
        return '\n'.join(cleaned_lines)