# AI Business Card Scanner

Ce projet expose une API FastAPI capable d'extraire les informations (nom, téléphone, email…)
d'une photo de carte de visite.

## Objectif (Plan Adnane)

1. **Optimisation OpenCV**
   - Prétraitement pensé pour photos prises au smartphone (faible luminosité, flou)
   - Ajustement de gamma, détection et correction de flou, enhancement de résolution, CLAHE
   - Correction d'inclinaison et débruitage intensif

2. **Précision OCR**
   - Tesseract configuré avec plusieurs modes de segmentation (PSM) et liste blanche
   - Passage de secours en très haute résolution si aucun texte détecté
   - **Option** : basculer sur EasyOCR (modèle CNN+transformer) en activant
     la variable d'environnement `ACTIVE_EASYOCR=true`
- Génération de variantes (inversion, dilatation, rotations) pour multiplier
  les chances d'une détection propre
- Calcul de confiance via `image_to_data` pour choisir le meilleur résultat

3. **Format JSON simplifié**
   - L'endpoint principal `/extract` retourne uniquement `nom`, `telephone` et `email`
   - Un modèle Pydantic `MinimalCardData` assure la conformité attendue par l'app mobile
   - L'endpoint de debug conserve toujours la structure complète et ajoute le format minimum


## Utilisation

1. Démarrer l'API :

```bash
uvicorn app.main:app --reload
```

2. Envoyer une image `POST /extract` ou `POST /extract/debug` via `curl`, `requests`, etc.

3. Exemple de test :

```bash
python tests/test_images/test.py path/to/card.jpg
```

---

Tous les modules sont écrits en Python et utilisent `opencv-python`, `pytesseract`,
et `fastapi`.
