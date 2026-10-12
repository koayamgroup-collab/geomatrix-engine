import json
import os
import ee
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="GeoMatrix AI Engine")

PROJECT_ID = "verdant-victory-429422-a7"


def init_gee():
  """Initialise Google Earth Engine avec le compte de service."""
  gee_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
  if not gee_json:
    raise Exception("Variable GEE_SERVICE_ACCOUNT_JSON introuvable.")

  if isinstance(gee_json, str):
    gee_json = gee_json.strip("'\"")

  credentials_info = json.loads(gee_json)
  credentials = ee.ServiceAccountCredentials(
      credentials_info["client_email"], key_data=gee_json
  )
  ee.Initialize(credentials, project=PROJECT_ID)


@app.on_event("startup")
def startup_event():
  try:
    init_gee()
    print("✅ GEE initialisé au démarrage avec succès")
  except Exception as e:
    print(f"❌ Erreur GEE au démarrage: {e}")


@app.get("/")
def home():
  return {"status": "online", "engine": "GeoMatrix AI Active"}


@app.post("/analyze")
async def analyze(request: Request):
  # S'assurer que GEE est initialisé pour la requête
  try:
    ee.Number(1).getInfo()
  except Exception:
    try:
      init_gee()
    except Exception as e:
      raise HTTPException(
          status_code=500, detail=f"Erreur d'initialisation GEE: {str(e)}"
      )

  try:
    data = await request.json()

    # Récupération des coordonnées du permis envoyées par Make/Airtable
    lat = float(data.get("latitude", 0))
    lon = float(data.get("longitude", 0))

    if lat == 0 or lon == 0:
      raise ValueError("Coordonnées latitude/longitude invalides ou manquantes.")

    # 1. Zone d'intérêt : Rayon de 5 km autour du point central du permis
    point = ee.Geometry.Point([lon, lat])
    roi = point.buffer(5000)

    # 2. Collection Sentinel-2 (Surface Reflectance) sans nuages
    s2_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate("2024-01-01", "2026-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
        .median()
        .clip(roi)
    )

    # 3. Calcul des indices minéralogiques et environnementaux
    # Bandes S2 : B4 (Rouge), B8 (NIR), B11 (SWIR1), B12 (SWIR2)
    iron_oxides = s2_collection.select("B11").divide(
        s2_collection.select("B4")
    )  # Oxydes de fer
    clays_index = s2_collection.select("B11").divide(
        s2_collection.select("B12")
    )  # Argiles / Hydroxyles
    ndvi = s2_collection.normalizedDifference(["B8", "B4"])  # Indice végétatif

    # 4. Extraction des moyennes statistiques sur la zone du permis
    mean_iron = iron_oxides.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=roi, scale=20
    ).get("B11")
    mean_clay = clays_index.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=roi, scale=20
    ).get("B11")
    mean_ndvi = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=roi, scale=20
    ).get("nd")

    val_iron = float(ee.Number(mean_iron).getInfo() or 0)
    val_clay = float(ee.Number(mean_clay).getInfo() or 0)
    val_ndvi = float(ee.Number(mean_ndvi).getInfo() or 0)

    # 5. Calcul d'un Score Global pondéré (0 à 100)
    # Pondération orientée prospection minière (fer + altérations argileuses)
    raw_score = (val_iron * 30) + (val_clay * 50) + (max(0, 1 - val_ndvi) * 20)
    final_score = round(min(max(raw_score, 12), 97.5), 2)

    return {
        "status": "success",
        "score_geomatrix": final_score,
        "metrics": {
            "indice_oxydes_fer": round(val_iron, 3),
            "indice_argiles": round(val_clay, 3),
            "indice_vegetation_ndvi": round(val_ndvi, 3),
        },
        "coordinates": {"lat": lat, "lon": lon},
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Erreur durant l'analyse GEE: {str(e)}"
    )
