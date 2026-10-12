from pydantic import BaseModel, root_validator
from typing import Optional, Union

class AnalysisRequest(BaseModel):
    lat: Optional[Union[float, str]] = None
    lng: Optional[Union[float, str]] = None
    coordinates: Optional[str] = None

    @root_validator(pre=True)
    extract_coords(cls, values):
        # Si un champ unique "Coordonnées_GPS" ou "coordinates" est passé sous forme "lat, lng"
        coords = values.get("coordinates") or values.get("lat")
        if isinstance(coords, str) and "," in coords:
            parts = coords.split(",")
            try:
                values["lat"] = float(parts[0].strip())
                values["lng"] = float(parts[1].strip())
            except ValueError:
                pass
        return values
