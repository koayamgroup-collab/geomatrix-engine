from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/analyze")
def analyze(lat: float = None, lng: float = None, Coordonnées_GPS: str = None):
    # Si les coordonnées sont envoyées sous forme de chaîne combinée "lat, lng" depuis Airtable
    if Coordonnées_GPS and "," in Coordonnées_GPS:
        parts = Coordonnées_GPS.split(",")
        try:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
        except ValueError:
            pass

    # Vérification finale
    if lat is None or lng is None:
        raise HTTPException(
            status_code=400, 
            detail="Géométrie ou coordonnées (lat/lng) manquantes dans la requête."
        )

    # Votre logique Google Earth Engine s'exécutera ici
    return {
        "status": "success",
        "latitude": lat,
        "longitude": lng,
        "message": "Analyse géologique effectuée avec succès."
    }
