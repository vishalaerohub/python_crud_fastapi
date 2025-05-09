from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, shutil, traceback, logging
from app.utils.database import read_db
from pathlib import Path
from app.utils.usbpath import find_usb_mount_path,box_base_path

router = APIRouter()
logger = logging.getLogger(__name__)

def safe_remove(path):
    try:
        os.remove(path)
        logger.info(f"Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"File not found: {path}")
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        traceback.print_exc()

#  Copy full folder with subfolders and files
def copy_folder_recursive(source: Path, destination: Path):
    if not source.exists():
        logger.warning(f"Source folder does not exist: {source}")
        return

    for item in source.iterdir():
        dest_item = destination / item.name
        try:
            if item.is_file():
                shutil.copy2(item, dest_item)
                logger.info(f"Copied file: {item.name}")
            elif item.is_dir():
                if dest_item.exists():
                    shutil.rmtree(dest_item)
                shutil.copytree(item, dest_item)
                logger.info(f"Copied folder: {item.name}")
        except Exception as e:
            logger.error(f"Failed to copy {item.name}: {e}")

@router.get("/sync-games")
def syncGames():
    games = read_db("games")
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

        # ===== Copy full folder structure for games =====
        try:
            usb_path = find_usb_mount_path()
            usb_games_path = Path(usb_path) / "content/games"
            dest_games_path = Path(f"{box_base_path()} games")

            dest_games_path.mkdir(parents=True, exist_ok=True)

            logger.info("Copying game files including folders...")
            copy_folder_recursive(usb_games_path, dest_games_path)

        except Exception as folder_err:
            logger.error(f"Error copying games folder: {folder_err}")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.critical(" Database error during syncGames", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error while syncing games")
    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
