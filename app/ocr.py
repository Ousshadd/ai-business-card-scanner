import pytesseract
from pytesseract import Output
import re
import logging
import cv2

# pour monter en résolution quand Tesseract échoue
from app.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

class OCREngine:
    """Moteur OCR - Tesseract par défaut mais possibilité de passer
    à EasyOCR (modèle CNN+transformer pré‑entraîné très performant).
    """

    def __init__(self, use_easyocr: bool = False):
        # switch entre moteur tesseract / easyocr
        self.use_easyocr = use_easyocr
        if self.use_easyocr:
            import easyocr
            # langues ouvertes à l'utilisateur
            self.easy_reader = easyocr.Reader(['fr', 'en'], gpu=False)  # activer gpu si disponible
        
        # Configuration pour Windows (décommente si besoin)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Langues supportées (français + anglais)
        self.langs = 'fra+eng'
        
        # Liste de caractères autorisés (améliore précision pour cartes)
        self.whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@.+-:/&" 
        
        # Différentes configurations de segmentation (PSM)
        self.psm_configs = [
            '--oem 3 --psm 0',      # Orientation et script détectés
            '--oem 3 --psm 1',      # Orientation
            '--oem 3 --psm 3',      # Automatique
            '--oem 3 --psm 4',      # Colonne
            '--oem 3 --psm 6',      # Bloc uniforme
            '--oem 3 --psm 7',      # Une seule ligne (utile pour télé/email)
            '--oem 3 --psm 11',     # Texte clairsemé
            '--oem 3 --psm 13',     # Sparse avec orientation
        ]
        
    def extract_text(self, image):
        """
        Extrait le texte d'une image prétraitée en multipliant les essais
        sur variantes et en choisissant le résultat à la confiance la plus
        élevée.
        """
        # si on veut un modèle plus performant que tesseract, on peut
        # basculer sur EasyOCR (pré‑entraîné, CNN+RNN/transformer, bien plus
        # précis sur les cartes modernes). Le flag `use_easyocr` doit être vrai
        # lors de l'initialisation.
        if self.use_easyocr:
            try:
                results = self.easy_reader.readtext(image)
                # results = [(bbox, text, confidence), ...]
                texts = [r[1] for r in results]
                combined = "\n".join(texts)
                logger.info(f"EasyOCR trouvé {len(texts)} blocs")
                return self._fix_common_mistakes(self._clean_text(combined))
            except Exception as e:
                logger.warning(f"EasyOCR erreur: {e}, fallback Tesseract")
                # on continue vers tesseract

        try:
            candidates = []  # tuples (text,confidence)

            # générer variantes via transformations simples
            variants = self._generate_variants(image)

            for idx, img in enumerate(variants):
                for config in self.psm_configs:
                    cfg = config + f" -c tessedit_char_whitelist={self.whitelist}"
                    text, conf = self._ocr_with_confidence(img, cfg)
                    if text and len(text.strip()) > 3:
                        candidates.append((text, conf))
                        logger.debug(f"Variante {idx}, config {config}: conf={conf:.1f}, len={len(text)}")

            # Si aucun candidat, faire un dernier essai en haute résolution
            if not candidates:
                try:
                    hires = ImagePreprocessor.enhance_resolution(image)
                    text, conf = self._ocr_with_confidence(hires, f"-c tessedit_char_whitelist={self.whitelist}")
                    if text:
                        candidates.append((text, conf))
                except Exception:
                    pass

            # choisir texte à la plus haute confiance
            if candidates:
                best_text, best_conf = max(candidates, key=lambda x: x[1])
            else:
                # fallback simple
                best_text = pytesseract.image_to_string(image, lang=self.langs)

            cleaned_text = self._clean_text(best_text)
            cleaned_text = self._fix_common_mistakes(cleaned_text)

            logger.info(f"OCR terminé: conf={best_conf if candidates else 'n/a'} len={len(cleaned_text)}")
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

    def _ocr_with_confidence(self, image, config):
        """Execute Tesseract et renvoie (texte, confiance moy.)."""
        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.langs,
                config=config,
                output_type=Output.DICT
            )
            texts = [t for t in data['text'] if t.strip()]
            confs = []
            for c in data.get('conf', []):
                try:
                    num = float(c)
                    confs.append(num)
                except Exception:
                    continue
            avg = sum(confs) / len(confs) if confs else 0.0
            return " ".join(texts), avg
        except Exception as e:
            logger.warning(f"Erreur confidences OCR: {e}")
            try:
                return pytesseract.image_to_string(image, lang=self.langs, config=config), 0.0
            except:
                return "", 0.0

    def _generate_variants(self, image):
        """Renvoie une liste d'images dérivées pour multiplier les chances.
        - inversion, légère dilatation, rotations.
        """
        variants = [image]
        try:
            inv = cv2.bitwise_not(image)
            variants.append(inv)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
            dil = cv2.dilate(image, kernel, iterations=1)
            variants.append(dil)
            # rotations 90° et 270°
            (h, w) = image.shape[:2]
            for angle in (90, 270):
                M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
                rot = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                variants.append(rot)
        except Exception:
            pass
        return variants