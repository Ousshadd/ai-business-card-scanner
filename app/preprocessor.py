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
            
            # 3. Débruiter (utile sur photos bruitées ou en basse lumière)
            denoised = cv2.fastNlMeansDenoising(gray, h=30)

            # 4. Ajustement de gamma / luminosité (mobile souvent sous-exposé)
            adjusted = ImagePreprocessor._adjust_gamma(denoised)

            # 5. Améliorer le contraste avec CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(adjusted)

            # 6. Détection et correction de flou
            if ImagePreprocessor._is_blurry(enhanced):
                logger.info("Image floue détectée, application d'un filtre de netteté")
                enhanced = ImagePreprocessor._sharpen(enhanced)

            # 7. Seuillage adaptatif (pour texte sur fond varié)
            binary = cv2.adaptiveThreshold(
                enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # 8. Enlever le bruit restant (opérations morphologiques)
            kernel = np.ones((1,1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # 9. Correction d'inclinaison
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
        """Améliore la résolution de l'image

        Utile lorsque l'OCR ne lit pas correctement les petites polices.
        """
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

    @staticmethod
    def _adjust_gamma(image, gamma=1.5):
        """Amplifie l'image pour corriger les photos sombres."""
        try:
            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255
                              for i in np.arange(0, 256)]).astype("uint8")
            return cv2.LUT(image, table)
        except Exception:
            return image

    @staticmethod
    def _is_blurry(image, thresh=100.0):
        """Retourne True si l'image semble floue (variance du Laplacien faible)."""
        try:
            lap = cv2.Laplacian(image, cv2.CV_64F)
            var = lap.var()
            return var < thresh
        except Exception:
            return False

    @staticmethod
    def _sharpen(image):
        """Applique un filtre de netteté simple."""
        kernel = np.array([[0, -1, 0],
                           [-1, 5,-1],
                           [0, -1, 0]])
        try:
            return cv2.filter2D(image, -1, kernel)
        except Exception:
            return image