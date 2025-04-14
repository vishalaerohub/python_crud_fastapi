from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
from app.utils.downloader import downloadAndSaveFile
import requests, os, logging, traceback

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

logger = logging.getLogger(__name__)

def safe_remove(path: str):
    try:
        os.remove(path)
        logger.info(f"✅ Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"⚠️ File not found (skipping): {path}")
    except Exception as e:
        logger.error(f"❌ Error removing file {path}: {e}")
        traceback.print_exc()

@router.get("/syncCityscape")
def sync_cityscape():
    API_URL = apiEndPointBaseUrl + "syncCityscape"

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="API call failed")

    if not data.get("data"):
        raise HTTPException(status_code=404, detail="Data is not available")

    output = []
    db = get_db_connection()
    cursor = db.cursor()

    try:
        for item in data["data"]:
            cityscape_id = item["id"]

            if item["is_deleted"] == 1:
                # Delete files
                pdf_path = os.path.join("public", "cityscape_pdf", os.path.basename(item["pdf_path"]))
                thumb_path = os.path.join("public", "cityscape_thumbnails", os.path.basename(item["thumbnail"]))

                safe_remove(pdf_path)
                safe_remove(thumb_path)
                
                cursor.execute("DELETE FROM city_scapes WHERE cityscape_id = %s", (cityscape_id,))
                logger.info(f"❌ Deleted cityscape ID {cityscape_id}")

            else:
                # Insert or update
                slug = item["city_name"].replace(" ", "-").lower()
                cityscape_data = (
                    cityscape_id,
                    item["city_name"],
                    slug,
                    item["thumbnail"],
                    item["pdf_path"],
                    str(item["status"])
                )

                cursor.execute("""
                    INSERT INTO city_scapes (
                        cityscape_id, city_name, cityscape_slug_url, thumbnail, pdf_path, status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        city_name=VALUES(city_name),
                        cityscape_slug_url=VALUES(cityscape_slug_url),
                        thumbnail=VALUES(thumbnail),
                        pdf_path=VALUES(pdf_path),
                        status=VALUES(status)
                """, cityscape_data)

                if item["pdf_path"]:
                    downloadAndSaveFile(item["pdf_path"], "cityscape_pdf")
                if item["thumbnail"]:
                    downloadAndSaveFile(item["thumbnail"], "cityscape_thumbnails")

                logger.info(f"✅ Synced cityscape ID {cityscape_id} - {item['city_name']}")
                output.append({
                    "cityscape_id": cityscape_id,
                    "message": f"{item['city_name']} synced successfully",
                    "status": "true",
                    "code": "200"
                })

        db.commit()
    except Exception as e:
        db.rollback()
        logger.critical("❌ DB error while syncing cityscape", exc_info=True)
        raise HTTPException(status_code=500, detail="Error while syncing cityscape")
    finally:
        db.close()

    return output
