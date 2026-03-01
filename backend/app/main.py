from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "L'API est opérationnelle ! tu peux maintenant commencer le développement mobile."}

@app.get("/health")
def health_check():
    # Hna ghadi n-tastiw men be3d wach Tesseract m-installer mzyan
    return {"status": "ok", "engine": "FastAPI"}