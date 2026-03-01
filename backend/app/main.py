from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()

# Hada model dyal l'data lli gha n-rjje3o l'mobile
class ContactBase(BaseModel):
    name: str
    phone: str
    email: str
    company: str

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

# HADA HOWA L'ENDPOINT /extract
@app.post("/extract", response_model=ContactBase)
async def extract_card_info(file: UploadFile = File(...)):
    # Hna Oussama gha y-stabel tsswira (Upload)
    # O hna Adnane gha y-zid l'logic dyal vision.py men be3d
    
    # Daba gha n-rjje3o Mock Data (data kdoubiya) bach t-testi l'mobile
    return {
        "name": "Oussama Test",
        "phone": "+212 600-000000",
        "email": "oussama@example.com",
        "company": "FSR Rabat"
    }