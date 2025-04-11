# Inside your FastAPI router

from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
from app.utils.downloader import downloadAndSaveFile
import requests
import traceback
import logging

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/syncMagazine")
def syncMagazine():
    API_URL = apiEndPointBaseUrl + "syncMagazine"
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

    if not response_data.get("data"):
        raise HTTPException(status_code=404, detail="Data is not available")

    if response_data.get("status") != 1:
        return {
            "data": "Data not available",
            "status": "false",
            "code": 404
        }

    output = []
    db = get_db_connection()

    try:
        cursor = db.cursor()
        for item in response_data["data"]:
            if item["status"] == "1":
                if item.get("path"):
                    saved_path = downloadAndSaveFile(item["path"], "magazines")
                    logger.info(f"PDF saved at: {saved_path}")
                if item.get("thumbnail"):
                    saved_thumb = downloadAndSaveFile(item["thumbnail"], "magazine_thumbnails")
                    logger.info(f"Thumbnail saved at: {saved_thumb}")

            magazine_data = (
                item["id"],
                item["name"],
                item["language"],
                item["path"],
                item["thumbnail"],
                item["status"],
                item["magazine_date"],
                item["size"],
                item["file_format"]
            )

            cursor.execute("""
                INSERT INTO magazines (
                    magazine_id, name, language, path, thumbnail, status, magazine_date, size, file_format
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    language=VALUES(language),
                    path=VALUES(path),
                    thumbnail=VALUES(thumbnail),
                    status=VALUES(status),
                    magazine_date=VALUES(magazine_date),
                    size=VALUES(size),
                    file_format=VALUES(file_format)
            """, magazine_data)

            output.append({
                "magazine_id": item["id"],
                "message": f"{item['name']} synced successfully"
            })

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("❌ DB Error during magazine sync", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
