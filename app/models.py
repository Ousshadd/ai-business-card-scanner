from pydantic import BaseModel
from typing import Optional

class CardData(BaseModel):
    """Modèle de données pour une carte de visite"""
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    societe: Optional[str] = None
    titre: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "nom": "Dupont",
                "prenom": "Jean",
                "telephone": "+212612345678",
                "email": "jean.dupont@company.com",
                "societe": "Company SA",
                "titre": "Directeur Commercial"
            }
        }