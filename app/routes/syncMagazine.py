from fastapi import APIRouter, HTTPException
import requests
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

@router.get("/sync-magazine")
def sync_magazine():
    API_URL = API_BASE_URL + "syncMagazine"
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch magazine data")
