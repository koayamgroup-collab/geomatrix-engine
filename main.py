from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/analyze")
async def analyze(request: Request):
    # Récupère soit le JSON, soit les paramètres d'URL, soit le corps brut
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    
    # Récupère aussi les query parameters si présents dans l'URL
    query_params = dict(request.query_params)
    
    print(f"📦 Corps JSON reçu : {body}")
    print(f"🔗 Paramètres URL reçus : {query_params}")

    lat = None
    lng = None

    # 1. Recherche dans le JSON (corps)
    if isinstance(body, dict):
        coords = body.get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            try:
                lat = float(coords[0])
                lng = float(coords[1])
            except ValueError:
                pass
        
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

    # 2. Recherche dans les paramètres d'URL si toujours introuvable
    if lat is None or lng is None:
        raw_gps = query_params.get("Coordonnées_GPS") or query_params.get("lat")
        if isinstance(raw_gps, str) and "," in raw_gps:
            parts = raw_gps.split(",")
            try:
                lat = float(parts.get("lat") if isinstance(parts, dict) else parts[0].strip())
                lng = float(parts[1].strip())
            except ValueError:
                pass

    if lat is None or lng is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Coordonnées introuvables. Reçu - JSON: {body} | URL: {query_params}"
        )

    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "message": "Analyse géologique effectuée avec succès."
    }
