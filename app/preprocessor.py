import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Classe pour le prétraitement des images avec OpenCV"""
    
    @staticmethod
    def preprocess(image_bytes):
        """
        Prétraite une image pour optimiser l'OCR
        
        Args:
            image_bytes: bytes de l'image
            
        Returns:
            image prétraitée (numpy array)
        """
        try:
            # Convertir bytes en image OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Impossible de décoder l'image")
            
            # 1. Redimensionner si trop grande (max 2000px)
            height, width = img.shape[:2]
            if width > 2000:
                scale = 2000 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height))
                logger.info(f"Image redimensionnée: {width}x{height} -> {new_width}x{new_height}")
            
            # 2. Convertir en gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 3. Débruiter
            denoised = cv2.fastNlMeansDenoising(gray, h=30)
            
            # 4. Améliorer le contraste avec CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 5. Seuillage adaptatif (pour texte sur fond varié)
            binary = cv2.adaptiveThreshold(
                enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 6. Enlever le bruit restant (opérations morphologiques)
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 7. Correction d'inclinaison
            cleaned = ImagePreprocessor._correct_skew(cleaned)
            
            logger.info("Prétraitement terminé avec succès")
            return cleaned
            
        except Exception as e:
            logger.error(f"Erreur dans le prétraitement: {str(e)}")
            raise
    
    @staticmethod
    def _correct_skew(image):
        """Corrige l'inclinaison de l'image"""
        try:
            # Trouver tous les points blancs (texte)
            coords = np.column_stack(np.where(image > 0))
            
            if len(coords) < 10:  # Pas assez de points
                return image
            
            # Calculer l'angle d'inclinaison
            angle = cv2.minAreaRect(coords)[-1]
            
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Ne corriger que si l'angle est significatif (> 0.5 degré)
            if abs(angle) < 0.5:
                return image
            
            # Appliquer la rotation
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            logger.info(f"Correction d'inclinaison: {angle:.2f} degrés")
            return rotated
            
        except Exception as e:
            logger.warning(f"Erreur dans correction d'inclinaison: {str(e)}")
            return image
    
    @staticmethod
    def enhance_resolution(image):
        """Améliore la résolution de l'image"""
        try:
            # Redimensionner avec interpolation pour meilleure qualité
            height, width = image.shape[:2]
            new_width = width * 2
            new_height = height * 2
            enhanced = cv2.resize(
                image, (new_width, new_height),
                interpolation=cv2.INTER_CUBIC
            )
            return enhanced
        except:
            return image