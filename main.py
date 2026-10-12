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
            val = values.get("lat")
            # Si lat contient une chaîne combinée "lat, lng"
            if isinstance(val, str) and "," in val:
                parts = val.split(",")
                try:
                    values["lat"] = float(parts[0].strip())
                    values["lng"] = float(parts[1].strip())
                except ValueError:
                    pass
        return values

@app.post("/analyze")
def analyze_location(data: AnalysisRequest):
    if data.lat is None or data.lng is None:
        raise HTTPException(status_code=400, detail="Géométrie ou coordonnées (lat/lng) manquantes dans la requête.")
    
    # Vos traitements Google Earth Engine ici
    return {
        "status": "success",
        "latitude": data.lat,
        "longitude": data.lng,
        "message": "Analyse géologique effectuée avec succès."
    }
