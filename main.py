import json
import os
import ee
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="GeoMatrix AI Engine")

# Nom du projet Google Cloud enregistre sur GEE
PROJECT_ID = "verdant-victory-429422-a7"


def authenticate_gee():
  """Fonction d'authentification robuste pour Google Earth Engine."""
  gee_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
  if not gee_json:
    raise ValueError("Variable d'environnement GEE_SERVICE_ACCOUNT_JSON introuvable.")

  credentials_info = json.loads(gee_json)
  credentials = ee.ServiceAccountCredentials(
      credentials_info["client_email"], key_data=gee_json
  )

  # Passer explicitement le projet Cloud est obligatoire sur les versions récentes de GEE
  ee.Initialize(credentials, project=PROJECT_ID)


@app.on_event("startup")
def initialize_gee_on_startup():
  """Initialisation au démarrage du serveur FastAPI."""
  try:
    authenticate_gee()
    print("✅ Google Earth Engine initialisé avec succès au démarrage !")
  except Exception as e:
    print(f"❌ Avertissement lors de l'initialisation GEE au démarrage: {e}")


def ensure_gee_initialized():
  """Vérifie si GEE est prêt, sinon tente une ré-initialisation immédiate."""
  try:
    # Test simple pour vérifier si la bibliothèque répond
    ee.Number(1).getInfo()
  except Exception:
    print("⚠️ GEE non initialisé, tentative de ré-initialisation...")
    try:
      authenticate_gee()
    except Exception as e:
      raise HTTPException(
          status_code=500,
          detail=f"Échec critique de l'initialisation Earth Engine: {str(e)}",
      )


@app.get("/")
def home():
  return {"status": "online", "service": "GeoMatrix AI Engine"}


# Exemple de structure de votre route /analyze
@app.post("/analyze")
async def analyze_permis(payload: dict):
  # Garantit que GEE est bien prêt avant de traiter le permis
  ensure_gee_initialized()

  try:
    # --- INSÉREZ VOTRE LOGIQUE DE TRAITEMENT GEE ICI ---
    # Exemple : point = ee.Geometry.Point([longitude, latitude])

    return {
        "status": "success",
        "message": "Analyse géospatiale exécutée avec succès",
    }
  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Erreur lors du traitement GEE: {str(e)}"
    )
