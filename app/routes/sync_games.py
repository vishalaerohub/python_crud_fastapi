from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, shutil, traceback, logging

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

logger = logging.getLogger(__name__)

def safe_remove(path):
    try:
        os.remove(path)
        logger.info(f"✅ Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"⚠️ File not found: {path}")
    except Exception as e:
        logger.error(f"❌ Error deleting file {path}: {e}")
        traceback.print_exc()

@router.get("/sync-games")
def syncGames():
    API_URL = apiEndPointBaseUrl + "syncGames"

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"❌ Failed to fetch games: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch game data")

    if not data.get("data"):
        raise HTTPException(status_code=404, detail="No game data available")

    games = data["data"]
    db = get_db_connection()
    cursor = db.cursor()
    output = []

    try:
        for game in games:
            game_id = game["id"]
            game["status"] = str(game["status"])
            game["is_deleted"] = str(game["is_deleted"])

            if game["is_deleted"] == "1":
                try:
                    game_path = os.path.join("public", game["src"].replace("index.html", "").lstrip("/"))
                    shutil.rmtree(game_path, ignore_errors=True)

                    cover_path = os.path.join("public", game["cover_src"].lstrip("/"))
                    safe_remove(cover_path)

                    cursor.execute("DELETE FROM games WHERE id = %s", (game_id,))
                    logger.info(f"🗑️ Deleted game ID {game_id}")
                except Exception as e:
                    logger.error(f"❌ Error deleting files for game {game_id}: {e}")
                    traceback.print_exc()
            else:
                cursor.execute("""
                    INSERT INTO games (id, title, src, cover_src, status, is_deleted, genre, Highlight, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        src = VALUES(src),
                        cover_src = VALUES(cover_src),
                        status = VALUES(status),
                        is_deleted = VALUES(is_deleted),
                        genre = VALUES(genre),
                        Highlight = VALUES(Highlight),
                        start_date = VALUES(start_date),
                        end_date = VALUES(end_date)
                """, (
                    game_id,
                    game.get("title", ""),
                    game.get("src", ""),
                    game.get("cover_src", ""),
                    game.get("status", "0"),
                    game.get("is_deleted", "0"),
                    game.get("genre", ""),
                    game.get("Highlight", ""),
                    game.get("start_date", ""),
                    game.get("end_date", "") 
                ))

                logger.info(f"✅ Synced game: {game['title']}")

                output.append({
                    "game_id": game_id,
                    "message": f"{game['title']} has been synced",
                    "status": "true"
                })

        db.commit()
    except Exception as e:
        db.rollback()
        logger.critical("❌ Database error during syncGames", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while syncing games")
    finally:
        db.close()

    return output
