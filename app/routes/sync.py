from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests
import os
import shutil
import traceback

import logging

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

@router.get("/syncMovies")
async def syncMovies():
    API_URL = apiEndPointBaseUrl + "syncMovies"

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
            ad_id = item["ad_id"] if item["ad_id"] not in [None, "", "0"] else None

            if item["is_deleted"] == "1":
                try:
                    shutil.rmtree(os.path.join("public", item["src"]), ignore_errors=True)
                    safe_remove(os.path.join("public", item["p_src"]))
                    safe_remove(os.path.join("public", item["bd_src"]))
                    logger.info(f"🗑️ Deleted files for movie ID {item['id']}")
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting files for movie ID {item['id']}: {e}")
                    traceback.print_exc()

                cursor.execute("DELETE FROM movies WHERE id = %s", (item["id"],))
                logger.info(f"❌ Deleted movie ID {item['id']} from database")

            else:
                movie_data = (
                    item["id"],
                    item["lang"],
                    item["title"],
                    item["media_type"],
                    item["genre"],
                    item["category"],
                    item["distributor"],
                    str(item["synopsis"]),
                    item["year"],
                    item["language"],
                    item["duration"],
                    item["TMDbId"],
                    item["src"],
                    item["p_src"],
                    item["bd_src"],
                    item["IMDB_rating"],
                    item["rating"],
                    item["Highlight"],
                    item["cast"],
                    item["direction"],
                    item["is_drm"],
                    item["fairplay_src"],
                    item["widewine_src"],
                    item["position"],
                    item["start_date"],
                    item["end_date"],
                    ad_id,
                    item["is_deleted"],
                    str(item["status"])
                )

                try:
                    cursor.execute("""
                        INSERT INTO movies (
                            id, lang, title, media_type, genre, category, distributor, synopsis, year, language, duration, TMDbId,
                            src, p_src, bd_src, IMDB_rating, rating, Highlight, cast, direction, is_drm, fairplay_src,
                            widewine_src, position, start_date, end_date, ad_id, is_deleted, status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON DUPLICATE KEY UPDATE
                            lang=VALUES(lang), title=VALUES(title), media_type=VALUES(media_type),
                            genre=VALUES(genre), category=VALUES(category), distributor=VALUES(distributor),
                            synopsis=VALUES(synopsis), year=VALUES(year), language=VALUES(language),
                            duration=VALUES(duration), TMDbId=VALUES(TMDbId), src=VALUES(src),
                            p_src=VALUES(p_src), bd_src=VALUES(bd_src), IMDB_rating=VALUES(IMDB_rating),
                            rating=VALUES(rating), Highlight=VALUES(Highlight), cast=VALUES(cast),
                            direction=VALUES(direction), is_drm=VALUES(is_drm),
                            fairplay_src=VALUES(fairplay_src), widewine_src=VALUES(widewine_src),
                            position=VALUES(position), start_date=VALUES(start_date), end_date=VALUES(end_date),
                            ad_id=VALUES(ad_id), is_deleted=VALUES(is_deleted), status=VALUES(status)
                    """, movie_data)

                    output.append({
                        "movie_id": item['id'],
                        "message": f"{item['title']} has been updated",
                        "status": "true",
                        "code": "200"
                    })
                    logger.info(f"✅ Upserted movie: {item['title']} (ID: {item['id']})")

                except Exception as e:
                    logger.error(f"❌ SQL Error for movie ID {item['id']}: {e}")
                    traceback.print_exc()
                    logger.debug("💡 Data causing error: %s", movie_data)

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

@router.get("/syncData")
def syncData():
    return {
        "data":"looking goooddd mannn..."
    }


