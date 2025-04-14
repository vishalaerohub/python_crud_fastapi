from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, logging, traceback
from app.utils.downloader import downloadAndSaveFile

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

def safe_remove(path: str):
    try:
        os.remove(path)
        logger.info(f"✅ Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"⚠️ File not found (skipping): {path}")
    except Exception as e:
        logger.error(f"❌ Error removing file {path}: {e}")
        traceback.print_exc()

@router.get("/sync-shopping")
async def sync_shopping():
    API_URL = apiEndPointBaseUrl + "syncShopping"

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
            # Download and save the shopping file
            downloadAndSaveFile(item['path'], "shoppingInfo")

            # Prepare data to update or insert into the database
            shopping_data = (
                item["id"],
                item["name"],
                os.path.basename(item["path"]), 
            )

            try:
                cursor.execute("""
                    INSERT INTO shoppinginfo (id, name, path)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name=VALUES(name),
                        path=VALUES(path)
                """, shopping_data)

                output.append({
                    "shopping_id": item['id'],
                    "message": f"'{item['name']}' has been updated",
                    "status": "true",
                    "code": "200"
                })
                logger.info(f"✅ Upserted shopping info: {item['name']} (ID: {item['id']})")

            except Exception as e:
                logger.error(f"❌ SQL Error for shopping item ID {item['id']}: {e}")
                traceback.print_exc()

        db.commit()

    except Exception as db_error:
        db.rollback()
        logger.critical("❌ Fatal DB error. Rolled back transaction.")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
