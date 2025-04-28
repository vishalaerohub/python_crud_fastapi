from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, traceback, logging
from pathlib import Path
from app.utils.getFileSize import list_files_with_sizes, list_folders_with_sizes
import shutil
from datetime import datetime

# Define logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define router
router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")

# Function to check if the folder exists
def check_folder_existence(folder_path: str):
    folder_path = Path(folder_path)
    print(f"Checking if the folder exists: {folder_path}")
    return folder_path.exists() and folder_path.is_dir()

@router.get("/sync-music")
def sync_music_router():
    API_URL = apiEndPointBaseUrl + "syncMusics"

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
    
    songs = response_data["data"]
    db = get_db_connection()
    cursor = db.cursor()
    output = []

    for song in songs:
        song_id = song["id"]
        is_deleted = song["is_deleted"]
        

        try:
            if is_deleted == 1:
                # Delete files
                song_path = os.path.join("public", song["song_path"].lstrip("/"))
                cover_path = os.path.join("public", song["cover_path"].lstrip("/"))
                if os.path.exists(song_path):
                    os.remove(song_path)
                if os.path.exists(cover_path):
                    os.remove(cover_path)

                # Delete DB record
                cursor.execute("DELETE FROM songs WHERE id = %s", (song_id,))
            else:
                # Convert datetime strings to MySQL format
                created_at = parse_date(song['createdAt'])
                updated_at = parse_date(song['updatedAt'])

                cursor.execute("""
                    INSERT INTO songs (
                        id, partner_id, title, genres, album, year, category, artist, status,
                        song_path, cover_path, playlist_id, is_deleted, position,
                        start_date, end_date, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        partner_id=VALUES(partner_id), title=VALUES(title), genres=VALUES(genres),
                        album=VALUES(album), year=VALUES(year), category=VALUES(category),
                        artist=VALUES(artist), status=VALUES(status), song_path=VALUES(song_path),
                        cover_path=VALUES(cover_path), playlist_id=VALUES(playlist_id), is_deleted=VALUES(is_deleted),
                        position=VALUES(position), start_date=VALUES(start_date), end_date=VALUES(end_date),
                        created_at=VALUES(created_at), updated_at=VALUES(updated_at)
                """, (
                    song_id, song["partner_id"], song["title"], song["genres"], song["album"], song["year"],
                    song["category"], song["artist"], str(song["status"]), song["song_path"], song["cover_path"],
                    song["playlist_id"], is_deleted, song["position"],
                    song["start_date"], song["end_date"], created_at, updated_at
                ))
                

                # ===== File Copy Logic =====
                usb_base_path = "/media/suhail/891D-C373/content/music_old/Songs"
                box_base_path = "/home/vishal/aerohub/python_crud_fastapi/public/Songs/"

                song_relative_path = song["song_path"].lstrip("/")
                file_name = os.path.basename(song_relative_path)

                try:
                    print("📁 song_path from API:", song["song_path"])
                    print("📁 Extracted file name:", file_name)
                    parts = song_relative_path.split("/")
                    if len(parts) < 3:
                        logger.warning(f"Invalid song_path format: {song['song_path']}")
                        continue

                    partner_folder = parts[1] 
                    source_path = Path(usb_base_path) / partner_folder / file_name
                    destination_path = Path(box_base_path) / partner_folder / file_name

                    print("🔍 Checking source:", source_path)
                    print("📌 Destination path:", destination_path)

                    if source_path.exists():
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, destination_path)
                        logger.info(f"✅ Copied: {file_name}")
                    else:
                        exists = "Not exists in box."
                        shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                        copy = f"Copied folder to: {final_destination}"
                else:
                    exists = "Folder does not exist in Pendrive."

                output.append({
                    "song_id": song_id,
                    "message": f"'{song['title']}' has been synced.",
                    "status": "true",
                    "code": "200",
                    "is_exists": exists,
                    "copied": copy
                })

        except Exception as e:
            traceback.print_exc()
            db.rollback()
            logger.error(f"❌ Error syncing song ID {song_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error syncing song ID {song_id}: {str(e)}")

    db.commit()
    db.close()

    return output
