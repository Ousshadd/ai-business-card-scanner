from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "L'API khdama! Oussama t-9der t-bda l'mobile daba."}

@app.get("/health")
def health_check():
    # Hna ghadi n-tastiw men be3d wach Tesseract m-installer mzyan
    return {"status": "ok", "engine": "FastAPI"}