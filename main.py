import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ee

app = FastAPI(title="GeoMatrix AI Engine")

try:
    ee.Initialize()
except Exception:
    pass

class PermisRequest(BaseModel):
    nom_permis: str
    coordinates: list

@app.get("/")
def home():
    return {"status": "GeoMatrix Engine active"}

@app.post("/analyze")
def analyze_permis(data: PermisRequest):
    try:
        aoi = ee.Geometry.Polygon(data.coordinates)
        
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi)
              .filterDate('2023-01-01', '2026-10-01')
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
              .median()
              .clip(aoi))

        iron_oxides = s2.select('B4').divide(s2.select('B2'))
        clay_minerals = s2.select('B11').divide(s2.select('B12'))
        
        srtm = ee.Image('USGS/SRTMGL1_003').clip(aoi)
        slope = ee.Terrain.slope(srtm)
        structural_density = slope.gt(15)

        geomatrix_score = (
            clay_minerals.unitScale(1.0, 2.5).multiply(0.35)
            .add(structural_density.multiply(0.30))
            .add(iron_oxides.unitScale(1.0, 2.0).multiply(0.20))
            .add(slope.unitScale(0, 45).multiply(0.15))
        ).multiply(100)

        mean_score = geomatrix_score.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=30,
            maxPixels=1e9
        ).get('GeoMatrix_Score').getInfo()

        map_url = geomatrix_score.getThumbURL({
            'region': aoi,
            'dimensions': 1024,
            'format': 'png',
            'palette': ['blue', 'cyan', 'green', 'yellow', 'orange', 'red']
        })

        return {
            "status": "success",
            "nom_permis": data.nom_permis,
            "score": round(mean_score, 2),
            "map_url": map_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
