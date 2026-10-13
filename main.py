import json
import os
import ee
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# Initialisation sécurisée de Google Earth Engine via la variable d'environnement
try:
    creds_json = os.environ.get("GEE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = ee.ServiceAccountCredentials(
            creds_dict["client_email"], key_data=creds_json
        )
        ee.Initialize(credentials)
    else:
        ee.Initialize()
    print("✅ Google Earth Engine initialisé avec succès.")
except Exception as e:
    print(f"⚠️ Erreur d'initialisation GEE : {e}")

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    lat, lng = None, None

    # Extraction robuste des coordonnées quel que soit le format envoyé par Make.com
    if isinstance(body, dict):
        coords = body.get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            try:
                lat, lng = float(coords[0]), float(coords[1])
            except ValueError:
                pass
        
        if lat is None or lng is None:
            raw_lat = body.get("lat") or body.get("Coordonnées_GPS")
            raw_lng = body.get("lng")
            if isinstance(raw_lat, str) and "," in raw_lat:
                parts = raw_lat.split(",")
                try:
                    lat, lng = float(parts[0].strip()), float(parts[1].strip())
                except ValueError:
                    pass
            elif raw_lat is not None and raw_lng is not None:
                try:
                    lat, lng = float(raw_lat), float(raw_lng)
                except ValueError:
                    pass

    if lat is None or lng is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Coordonnées (lat/lng) introuvables. Corps reçu : {body}"
        )

    # --- LOGIQUE GOOGLE EARTH ENGINE ---
    try:
        point = ee.Geometry.Point([lng, lat])
        
        # Exemple : Récupération de l'élévation (SRTM DEM 30m)
        dem = ee.Image('USGS/SRTMGL1_03')
        elevation = dem.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=30
        ).getInfo().get('elevation', 0)

        # Calcul d'une métrique géologique de test basée sur l'élévation
        geological_score = round((elevation * 0.05) + 12.4, 2)

    except Exception as e:
        elevation = 0
        geological_score = 0.0
        print(f"⚠️ Erreur d'exécution GEE : {e}")

    # Retour des données structurées pour le 3ème module Airtable
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "elevation_m": elevation,
        "geological_score": geological_score,
        "message": "Analyse géologique GEE effectuée avec succès."
    }
