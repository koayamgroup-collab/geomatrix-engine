import json
import os
import ee
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# Initialisation de Google Earth Engine
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

    # Extraction des coordonnées
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

    # --- LOGIQUE GOOGLE EARTH ENGINE (Élévation + NDVI) ---
    elevation = 0
    ndvi_value = 0.0
    geological_score = 0.0

    try:
        point = ee.Geometry.Point([lng, lat])
        region = point.buffer(100) # Zone d'analyse de 100 mètres autour du point

        # 1. Élévation (SRTM DEM)
        dem = ee.Image('USGS/SRTMGL1_03')
        elevation = dem.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=30
        ).getInfo().get('elevation', 0) or 0

        # 2. Indice NDVI (Sentinel-2 Surface Reflectance)
        # Bandes: B8 (Infrarouge Proche - NIR), B4 (Rouge)
        s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(region) \
            .filterDate('2025-01-01', '2026-12-31') \
            .sort('CLOUDY_PIXEL_PERCENTAGE') \
            .first()
        
        if s2:
            ndvi_image = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
            ndvi_dict = ndvi_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10
            ).getInfo()
            ndvi_value = round(ndvi_dict.get('NDVI', 0.0) or 0.0, 4)

        # 3. Score géologique / environnemental combiné
        geological_score = round((elevation * 0.02) + (ndvi_value * 15.0) + 10.0, 2)

    except Exception as e:
        print(f"⚠️ Erreur d'exécution GEE : {e}")

    # Retour des données structurées pour Airtable
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "elevation_m": round(elevation, 2),
        "ndvi": ndvi_value,
        "geological_score": geological_score,
        "message": "Analyse géologique et NDVI effectuée avec succès."
    }
