from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

app = FastAPI()

class AnalysisRequest(BaseModel):
    lat: Optional[Any] = None
    lng: Optional[Any] = None
    geometry: Optional[Any] = None
    Coordonnées_GPS: Optional[Any] = None

@app.post("/analyze")
async def analyze(request: Request):
    # Récupération brute du corps de la requête pour analyse dans les logs
    try:
        body = await request.json()
    except Exception:
        body = await request.body()
    
    print(f"📦 Corps brut reçu de Make.com : {body}")

    lat = None
    lng = None

    if isinstance(body, dict):
        # Cherche dans les différents noms de champs possibles envoyés par Make
        raw_lat = body.get("lat") or body.get("Coordonnées_GPS")
        raw_lng = body.get("lng")

        # Si les coordonnées sont combinées dans un seul champ (ex: "lat, lng")
        if isinstance(raw_lat, str) and "," in raw_lat:
            parts = raw_lat.split(",")
            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
            except ValueError:
                pass
        elif raw_lat is not None and raw_lng is not None:
            try:
                lat = float(str(raw_lat).strip())
                lng = float(str(raw_lng).strip())
            except ValueError:
                pass

    print(f"🔍 Valeurs extraites -> lat={lat}, lng={lng}")

    if lat is None or lng is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Géométrie ou coordonnées (lat/lng) manquantes dans la requête. Corps reçu : {body}"
        )

    # Votre logique Google Earth Engine ici
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "message": "Analyse géologique effectuée avec succès."
    }
