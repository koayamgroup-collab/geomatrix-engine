from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional, Union

app = FastAPI()

class AnalysisRequest(BaseModel):
    lat: Optional[Union[float, str]] = None
    lng: Optional[Union[float, str]] = None

    @model_validator(mode='before')
    @classmethod
    def parse_coords(cls, values):
        if isinstance(values, dict):
            # Récupère la valeur depuis "lat" ou un champ combiné équivalent
            val = values.get("lat")
            if isinstance(val, str) and "," in val:
                parts = val.split(",")
                try:
                    values["lat"] = float(parts[0].strip())
                    values["lng"] = float(parts[1].strip())
                except ValueError:
                    pass
            # Si les deux valeurs sont passées séparément mais sous forme de chaînes
            elif isinstance(values.get("lat"), str) and isinstance(values.get("lng"), str):
                try:
                    values["lat"] = float(values["lat"].strip())
                    values["lng"] = float(values["lng"].strip())
                except ValueError:
                    pass
        return values

@app.post("/analyze")
def analyze_location(data: AnalysisRequest):
    if data.lat is None or data.lng is None:
        raise HTTPException(
            status_code=400, 
            detail="Géométrie ou coordonnées (lat/lng) manquantes dans la requête."
        )
    
    # Votre logique Google Earth Engine s'exécutera ici avec data.lat et data.lng
    return {
        "status": "success",
        "latitude": data.lat,
        "longitude": data.lng,
        "message": "Analyse géologique effectuée avec succès."
    }
