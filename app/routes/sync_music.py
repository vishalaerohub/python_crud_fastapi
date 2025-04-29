from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests
import os
import traceback
import logging
from pathlib import Path
from app.utils.getFileSize import list_files_with_sizes
import shutil
from datetime import datetime
from app.utils.dateParse import parse_date
from app.utils.usbpath import find_usb_mount_path

usb_path = find_usb_mount_path()

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# FastAPI router
router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}


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
        raise HTTPException(status_code=404, detail="No data available")

    songs = response_data["data"]
    db = get_db_connection()
    cursor = db.cursor()
    output = []

    for song in songs:
        song_id = song["id"]
        is_deleted = song["is_deleted"]

        try:
            if is_deleted == 1:
                # Delete media files
                song_path = os.path.join("public", song["song_path"].lstrip("/"))
                cover_path = os.path.join("public", song["cover_path"].lstrip("/"))
                if os.path.exists(song_path):
                    os.remove(song_path)
                if os.path.exists(cover_path):
                    os.remove(cover_path)

                # Delete from DB
                cursor.execute("DELETE FROM songs WHERE id = %s", (song_id,))
            else:
                # Parse dates
                created_at = parse_date(song['createdAt'])
                updated_at = parse_date(song['updatedAt'])

                # Insert or update DB
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
                usb_base_path = f"{usb_path}/content/music/Songs"
                box_base_path = "/home/suhail/Python_Project/python_crud_fastapi/public/music/Songs/"

                song_relative_path = song["song_path"].lstrip("/")
                file_name = os.path.basename(song_relative_path)
                try:
                    parts = song_relative_path.split("/")
                    if len(parts) < 3:
                        logger.warning(f"Invalid song_path format: {song['song_path']}")
                        continue

                    source_path = Path(usb_base_path) / file_name
                    destination_path = Path(box_base_path) / file_name

                    if source_path.exists():
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, destination_path)
                        logger.info(f"✅ Copied: {file_name}")
                    else:
                        logger.warning(f"⚠️ Source file not found: {source_path}")
                except Exception as copy_err:
                    logger.error(f"❌ Error copying file {file_name}: {copy_err}")

                output.append({
                    "song_id": song['id'],
                    "title": song['title'],
                    "message": f"'{song['title']}' has been synced.",
                    "status": "true",
                    "code": "200"
                })

        except Exception as e:
            traceback.print_exc()
            db.rollback()
            logger.error(f"❌ Error syncing song ID {song_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error syncing song ID {song_id}: {str(e)}")

    # ===== Copy cover and poster folders =====
    try:
        usb_cover_path = Path(usb_path) / "content/music/cover"
        usb_poster_path = Path(usb_path) / "content/music/poster"
        dest_cover_path = Path("public/cover")
        dest_poster_path = Path("public/poster")

        dest_cover_path.mkdir(parents=True, exist_ok=True)
        dest_poster_path.mkdir(parents=True, exist_ok=True)

        def copy_folder(source: Path, destination: Path):
            if not source.exists():
                logger.warning(f"⚠️ Source folder does not exist: {source}")
                return
            for file in source.iterdir():
                if file.is_file():
                    dest_file = destination / file.name
                    shutil.copy2(file, dest_file)
                    logger.info(f"✅ Copied: {file.name} to {destination}")

        logger.info("📁 Copying cover images...")
        copy_folder(usb_cover_path, dest_cover_path)

        logger.info("📁 Copying poster images...")
        copy_folder(usb_poster_path, dest_poster_path)

    except Exception as folder_err:
        logger.error(f"❌ Error copying cover/poster folders: {folder_err}")

    # ===== Handle Missing Content =====
    try:
        logger.info("🔎 Handling missing content...")

        # 1. Check missing files in box
        cursor.execute("SELECT id, title, song_path FROM songs WHERE is_deleted = 0")
        db_songs = cursor.fetchall()
        missing_files = []

        for db_song in db_songs:
            song_id, title, song_path = db_song
            local_song_path = Path("public") / song_path.lstrip("/")
            if not local_song_path.exists():
                missing_files.append({"id": song_id, "title": title, "missing_path": str(local_song_path)})
                logger.warning(f"❌ Missing file for DB song: {title} at {local_song_path}")

        # 2. Compare USB and box folders
        usb_folder = Path(usb_path) / "content/music/Songs"
        box_folder = Path("public/music/Songs")

        def list_file_names(folder: Path):
            return sorted([f.name for f in folder.iterdir() if f.is_file()]) if folder.exists() else []

        usb_files = list_file_names(usb_folder)
        box_files = list_file_names(box_folder)

        usb_set = set(usb_files)
        box_set = set(box_files)

        only_in_usb = usb_set - box_set
        only_in_box = box_set - usb_set

        if only_in_usb:
            logger.warning(f"🟡 Files present in USB but missing in box: {only_in_usb}")
        if only_in_box:
            logger.warning(f"🟡 Files present in box but missing in USB: {only_in_box}")

        # 3. Compare folder sizes
        def folder_size_mb(folder: Path):
            return sum(f.stat().st_size for f in folder.glob("**/*") if f.is_file()) / (1024 * 1024)

        usb_size = folder_size_mb(usb_folder)
        box_size = folder_size_mb(box_folder)

        logger.info(f"📦 USB size: {usb_size:.2f} MB | Box size: {box_size:.2f} MB")

        output.append({
            "missing_files_in_box": missing_files,
            "usb_extra_files": list(only_in_usb),
            "box_extra_files": list(only_in_box),
            "usb_folder_size_MB": round(usb_size, 2),
            "box_folder_size_MB": round(box_size, 2)
        })

    except Exception as handle_err:
        logger.error(f"❌ Error handling missing content: {handle_err}")

    db.commit()
    db.close()
    return output
