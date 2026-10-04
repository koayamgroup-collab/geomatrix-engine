import json
import os
import ee
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="GeoMatrix AI Engine")

PROJECT_ID = "verdant-victory-429422-a7"


def init_gee():
  """Initialise Google Earth Engine avec le fichier JSON de la variable d'environnement."""
  gee_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
  if not gee_json:
    raise Exception("Variable GEE_SERVICE_ACCOUNT_JSON introuvable.")

  # Si la chaîne contient des guillemets d'échappement
  if isinstance(gee_json, str):
    gee_json = gee_json.strip("'\"")

  credentials_info = json.loads(gee_json)
  credentials = ee.ServiceAccountCredentials(
      credentials_info["client_email"], key_data=gee_json
  )

  # Initialisation avec le projet Cloud obligatoire
  ee.Initialize(credentials, project=PROJECT_ID)


@app.on_event("startup")
def startup_event():
  try:
    init_gee()
    print("✅ GEE initialisé au démarrage")
  except Exception as e:
    print(f"❌ Erreur GEE au démarrage: {e}")


@app.get("/")
def home():
  return {"status": "online"}


@app.post("/analyze")
async def analyze(request: Request):
  # 1. Re-garantir l'initialisation GEE pour la requête en cours
  try:
    ee.Number(1).getInfo()
  except Exception:
    try:
      init_gee()
    except Exception as e:
      raise HTTPException(
          status_code=500, detail=f"Erreur d'initialisation GEE: {str(e)}"
      )

  # 2. Récupérer les données envoyées par Make.com
  try:
    data = await request.json()
  except Exception:
    data = {}

  try:
    # --- VOTRE LOGIQUE GEE ICI ---
    # Exemple de test rapide de calcul Earth Engine:
    test_val = ee.Number(10).add(20).getInfo()

    return {
        "status": "success",
        "result_test": test_val,
        "received_data": data,
    }
  except Exception as e:
    # Capture l'erreur exacte pour la renvoyer proprement à Make
    raise HTTPException(
        status_code=500, detail=f"Erreur durant l'analyse GEE: {str(e)}"
    )
