from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    lat = None
    lng = None

    if isinstance(body, dict):
        # Récupère depuis la liste "coordinates" si elle existe (ex: [47.9029, 1.9092])
        coords = body.get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            try:
                lat = float(coords[0])
                lng = float(coords[1])
            except ValueError:
                pass
        
        # Fallback si les champs lat/lng séparés sont présents
        if lat is None or lng is None:
            raw_lat = body.get("lat") or body.get("Coordonnées_GPS")
            raw_lng = body.get("lng")
            if isinstance(raw_lat, str) and "," in raw_lat:
                parts = raw_lat.split(",")
                try:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                except ValueError:
                    pass
            elif raw_lat is not None and raw_lng is not None:
                try:
                    lat = float(raw_lat)
                    lng = float(raw_lng)
                except ValueError:
                    pass

    if lat is None or lng is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Géométrie ou coordonnées (lat/lng) manquantes dans la requête. Corps reçu : {body}"
        )

    # Votre logique Google Earth Engine s'exécutera ici
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "message": "Analyse géologique effectuée avec succès."
    }
