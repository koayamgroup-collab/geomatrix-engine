import os
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ee
import json

app = FastAPI(title="GeoMatrix GEE Engine")

# Initialisation de Google Earth Engine au démarrage
@app.on_event("startup")
def startup_event():
    try:
        # Si vous utilisez une variable d'environnement pour stocker le JSON du service account
        service_account_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
        if service_account_json:
            credentials_info = json.loads(service_account_json)
            credentials = ee.ServiceAccountCredentials(
                credentials_info.get("client_email"),
                key_data=service_account_json
            )
            ee.Initialize(credentials)
        else:
            # Initialisation par défaut (si les identifiants sont configurés autrement sur Render)
            ee.Initialize()
        print("GEE initialisé au démarrage avec succès")
    except Exception as e:
        print("Erreur lors de l'initialisation de GEE :")
        traceback.print_exc()

# Modèle de données correspondant à ce que Make.com envoie
class AnalysisRequest(BaseModel):
    lat: float = None
    lng: float = None
    geometry: dict = None
    # Ajoutez d'autres champs si nécessaire selon votre base Airtable

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        print(f"Requête reçue de Make.com : {request}")
        
        # Exemple de logique GEE (à adapter selon vos calculs d'indices spectraux)
        # 1. Définition de la zone d'intérêt (ROI)
        if request.geometry:
            roi = ee.Geometry(request.geometry)
        elif request.lat is not None and request.lng is not None:
            roi = ee.Geometry.Point([request.lng, request.lat]).buffer(1000)
        else:
            raise ValueError("Géométrie ou coordonnées (lat/lng) manquantes dans la requête.")

        # 2. Traitement Sentinel-2 / Indices (Exemple simplifié)
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate('2025-01-01', '2026-12-31')
            .sort('CLIFY_PIXEL_PERCENTAGE')
            .first()
        )
        
        # Vérification si une image est trouvée
        if collection.getInfo() is None:
            raise ValueError("Aucune image satellite trouvée pour cette zone et cette période.")

        # Calculs spectraux (Oxydes de fer, Argiles, etc.)
        # ... Votre logique de calcul GEE ici ...
        
        # Valeurs fictives ou issues de vos calculs GEE :
        iron_oxides_score = 0.75
        clays_score = 0.62
        global_score = 0.68

        # Résultat renvoyé à Make.com pour mise à jour dans Airtable
        return {
            "status": "success",
            "iron_oxides": iron_oxides_score,
            "clays": clays_score,
            "global_score": global_score
        }

    except Exception as e:
        # Affiche la trace complète en rouge dans les logs Render
        print("❌ Erreur critique dans /analyze :")
        traceback.print_exc()
        
        # Renvoie l'erreur détaillée pour l'analyser dans Make ou l'interface
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "Geomatrix API is running"}
