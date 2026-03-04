import pytesseract
import re
import logging

# pour monter en résolution quand Tesseract échoue
from app.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

class OCREngine:
    """Moteur OCR utilisant Tesseract"""
    
    def __init__(self):
        # Configuration pour Windows (décommente si besoin)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Langues supportées (français + anglais)
        self.langs = 'fra+eng'
        
        # Liste de caractères autorisés (améliore précision pour cartes)
        self.whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@.+-:/&" 
        
        # Différentes configurations de segmentation (PSM)
        self.psm_configs = [
            '--oem 3 --psm 6',      # Bloc de texte uniforme
            '--oem 3 --psm 4',      # Texte sur une colonne
            '--oem 3 --psm 3',      # Détection automatique
            '--oem 3 --psm 1',      # Détection avec orientation
            '--oem 3 --psm 11',     # Texte clairsemé / sparse text
            '--oem 3 --psm 7',      # Une seule ligne (utile pour tél/email)
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
                cfg = config + f" -c tessedit_char_whitelist={self.whitelist}"
                text = pytesseract.image_to_string(
                    image,
                    lang=self.langs,
                    config=cfg
                )
                if text and len(text.strip()) > 5:  # Garder si texte significatif
                    all_texts.append(text)
                    logger.info(f"Configuration {config} (whitelist appliquée): {len(text)} caractères")
            
            # Si aucun texte significatif, essayer avec résolution augmentée
            if not all_texts:
                logger.info("Aucun texte significatif détecté, tentative de suréchantillonnage")
                try:
                    hires = ImagePreprocessor.enhance_resolution(image)
                    text = pytesseract.image_to_string(hires, lang=self.langs, config=f"-c tessedit_char_whitelist={self.whitelist}")
                    all_texts.append(text)
                except Exception:
                    pass
            
            # Prendre le texte le plus long (souvent le meilleur)
            if all_texts:
                best_text = max(all_texts, key=len)
            else:
                # Fallback: essayer sans configuration spécifique
                best_text = pytesseract.image_to_string(image, lang=self.langs)
            
            # Nettoyer le texte
            cleaned_text = self._clean_text(best_text)
            # Corriger certaines erreurs fréquentes de Tesseract
            cleaned_text = self._fix_common_mistakes(cleaned_text)
            
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

    def _fix_common_mistakes(self, text):
        """Corrige des erreurs classiques (O/0, l/1, etc.)"""
        if not text:
            return text
        subs = {
            'O': '0',
            'o': '0',
            'l': '1',
            'I': '1',
            '¡': '1',
        }
        for k, v in subs.items():
            text = text.replace(k, v)
        # corriger email mal espacés
        text = text.replace(' at ', '@').replace(' dot ', '.')
        return text