from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import Optional

# Initialisation de l'application FastAPI
app = FastAPI()

# Modèle de données pour valider les informations de contact
# Ce modèle est utilisé pour l'envoi vers le mobile et la réception du mobile
class ContactBase(BaseModel):
    name: str
    phone: str
    email: str
    company: str

# Route de base pour vérifier que le serveur fonctionne
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

# --- ÉTAPE 1: EXTRACTION ---
# Endpoint pour recevoir l'image de la carte et renvoyer les textes extraits
@app.post("/extract", response_model=ContactBase)
async def extract_card_info(file: UploadFile = File(...)):
    """
    Cette fonction reçoit le fichier image envoyé par Flutter.
    Plus tard, Adnane ajoutera ici la logique OCR (EasyOCR/Tesseract).
    """
    # Simulation de données extraites (Mock Data) pour tester l'application mobile
    return {
        "name": "Oussama Test",
        "phone": "+212 600-000000",
        "email": "oussama@example.com",
        "company": "FSR Rabat"
    }

# --- ÉTAPE 2: ENREGISTREMENT ---
# Endpoint pour enregistrer les informations après validation sur le mobile
# C'est cette route qui manquait et qui causait l'erreur 404
@app.post("/save_contact")
async def save_contact(contact: ContactBase):
    """
    Reçoit les données JSON validées par l'utilisateur sur son téléphone.
    Adnane ajoutera ici la logique de base de données (SQLite/PostgreSQL).
    """
    # Affichage dans les logs Docker pour vérifier la réception
    print(f"DEBUG: Tentative d'enregistrement pour : {contact.name}")
    
    # Réponse de succès renvoyée au mobile
    return {
        "status": "success", 
        "message": f"Le contact {contact.name} a été enregistré avec succès dans le backend !"
    }