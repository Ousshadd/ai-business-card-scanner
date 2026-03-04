from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from typing import Optional

# Importer tes modules
from app.models import CardData, MinimalCardData
from app.preprocessor import ImagePreprocessor
from app.ocr import OCREngine
from app.parser import CardParser

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title="AI Business Card Scanner API",
    description="API pour extraire automatiquement les informations des cartes de visite",
    version="1.0.0"
)

# CORS pour Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par l'URL de l'app Flutter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser les composants
preprocessor = ImagePreprocessor()
# utilisation du modèle OCR performant si variable d'environnement ACTIVE_EASYOCR=true
import os
use_easy = os.getenv('ACTIVE_EASYOCR', 'false').lower() in ('1','true','yes')
ocr_engine = OCREngine(use_easyocr=use_easy)
parser = CardParser()

@app.get("/")
async def root():
    """Endpoint de test"""
    return {
        "message": "API Card Scanner prête",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Vérifier que l'API fonctionne"""
    return {"status": "healthy"}

@app.post("/extract", response_model=MinimalCardData)
async def extract_card(
    file: UploadFile = File(..., description="Image de la carte de visite")
):
    """
    Extrait les informations d'une carte de visite
    
    - **file**: Image de la carte (JPG, PNG)
    
    Retourne un JSON avec les champs: nom, prenom, telephone, email, societe, titre
    """
    try:
        logger.info(f"📸 Nouvelle requête: {file.filename}")
        
        # Vérifier le type de fichier
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être une image"
            )
        
        # 1. Lire l'image
        image_bytes = await file.read()
        logger.info(f"Image lue: {len(image_bytes)} bytes")
        
        # 2. Prétraitement OpenCV
        logger.info("🖼️ Étape 1: Prétraitement OpenCV...")
        processed_img = preprocessor.preprocess(image_bytes)
        
        # 3. OCR avec Tesseract
        logger.info("🔤 Étape 2: OCR Tesseract...")
        text = ocr_engine.extract_text(processed_img)
        logger.info(f"Texte extrait:\n{text}")
        
        # 4. Parsing avec Regex
        logger.info("🔍 Étape 3: Parsing...")
        data = parser.parse(text)
        logger.info(f"Données extraites: {data}")
        
        # 5. Construire format minimal pour mobile
        nom_val = None
        if data.get('nom') and data.get('prenom'):
            nom_val = f"{data['prenom']} {data['nom']}"
        else:
            nom_val = data.get('nom') or data.get('prenom')

        minimal = {
            'nom': nom_val,
            'telephone': data.get('telephone'),
            'email': data.get('email')
        }
        return MinimalCardData(**minimal)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )

@app.post("/extract/debug")
async def extract_debug(file: UploadFile = File(...)):
    """
    Version debug qui retourne plus d'informations
    Utile pour tester et améliorer l'OCR
    """
    try:
        image_bytes = await file.read()
        
        # Prétraitement
        processed_img = preprocessor.preprocess(image_bytes)
        
        # OCR
        text = ocr_engine.extract_text(processed_img)
        lines = [line for line in text.split('\n') if line.strip()]
        
        # Parsing
        parsed = parser.parse(text)
        # créer aussi un format minimal
        nom_val = None
        if parsed.get('nom') and parsed.get('prenom'):
            nom_val = f"{parsed['prenom']} {parsed['nom']}"
        else:
            nom_val = parsed.get('nom') or parsed.get('prenom')
        minimal = {
            'nom': nom_val,
            'telephone': parsed.get('telephone'),
            'email': parsed.get('email')
        }
        
        return {
            "filename": file.filename,
            "text_brut": text,
            "lignes": lines,
            "nombre_lignes": len(lines),
            "donnees_extraites": parsed,
            "minimal": minimal,
            "status": "success"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            }
        )

@app.get("/info")
async def info():
    """Informations sur l'API"""
    return {
        "name": "AI Business Card Scanner",
        "version": "1.0.0",
        "description": "Extraction automatique des cartes de visite",
        "technologies": ["FastAPI", "OpenCV", "Tesseract", "Regex"],
        "author": "Adnane El Harti",
        "endpoints": {
            "/": "GET - Test",
            "/health": "GET - Health check",
            "/extract": "POST - Extraire une carte",
            "/extract/debug": "POST - Version debug",
            "/info": "GET - Cette information"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Mode développement
        log_level="info"
    )