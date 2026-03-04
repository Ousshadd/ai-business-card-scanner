import requests
import json
import sys

def test_extract(image_path):
    """Teste l'endpoint extract avec une image"""
    
    url = "http://localhost:8000/extract"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/jpeg')}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            print("✅ Succès!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_debug(image_path):
    """Teste l'endpoint debug"""
    
    url = "http://localhost:8000/extract/debug"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path, f, 'image/jpeg')}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("✅ Debug - Succès!")
            print(f"Lignes trouvées: {data['nombre_lignes']}")
            print("Texte brut:")
            print(data['text_brut'])
            print("\nDonnées extraites:")
            print(json.dumps(data['donnees_extraites'], indent=2, ensure_ascii=False))
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path> [debug]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "debug":
        test_debug(image_path)
    else:
        test_extract(image_path)