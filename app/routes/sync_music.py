from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import os
import traceback
import logging
from pathlib import Path
import shutil

import requests

from app.utils.getFileSize import list_files_with_sizes
from app.utils.dateParse import parse_date
from app.utils.usbpath import find_usb_mount_path
from app.utils.database import read_db

# USB mount path
usb_path = find_usb_mount_path()

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# FastAPI router
router = APIRouter()

@router.get("/sync-music")
def sync_music_router():
    songs = read_db("Songs")

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
                created_at = parse_date(song.get("createdAt")) if song.get("createdAt") else None
                updated_at = parse_date(song.get("updatedAt")) if song.get("updatedAt") else None

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
                    song.get("start_date"), song.get("end_date"), created_at, updated_at
                ))

                # ===== File Copy with Size Check =====
                exists = ""
                copied = ""
                usb_base_path = Path(usb_path) / "content/music/Songs"

                box_base_path = Path("/home/suhail/Python_Project/python_crud_fastapi/public/music/Songs")


                song_relative_path = song["song_path"].lstrip("/")
                file_name = os.path.basename(song_relative_path)

                source_path = usb_base_path / file_name
                destination_path = box_base_path / file_name

                if source_path.exists():
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    src_size = source_path.stat().st_size

                    if destination_path.exists():
                        dst_size = destination_path.stat().st_size
                        if src_size != dst_size:
                            shutil.copy2(source_path, destination_path)
                            copied = f"File copied: {file_name}"
                            logger.info(copied)
                        else:
                            exists = f"File already exists with same size: {file_name}"
                            logger.info(exists)
                    else:
                        shutil.copy2(source_path, destination_path)
                        copied = f"File copied: {file_name}"
                        logger.info(copied)
                else:
                    logger.warning(f"Source file not found: {source_path}")

                output.append({
                    "song_id": song['id'],
                    "title": song['title'],
                    "message": f"'{song['title']}' has been synced.",
                    "status": "true",
                    "code": "200",
                    "is_exists": exists,
                    "copied": copied
                })

        except Exception as e:
            traceback.print_exc()
            db.rollback()
            logger.error(f"❌ Error syncing song ID {song_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error syncing song ID {song_id}: {str(e)}")

    # ===== Cover and Poster Folder Copy =====
    try:
        usb_cover_path = Path(usb_path) / "content/music/cover"
        usb_poster_path = Path(usb_path) / "content/music/poster"
        dest_cover_path = Path("/home/suhail/Python_Data/python_crud_fastapi/public/music/cover")
        dest_poster_path = Path("/home/suhail/Python_Data/python_crud_fastapi/public/music/poster")

        dest_cover_path.mkdir(parents=True, exist_ok=True)
        dest_poster_path.mkdir(parents=True, exist_ok=True)

        def copy_folder(source: Path, destination: Path):
            if not source.exists():
                logger.warning(f" Source folder does not exist: {source}")
                return
            for file in source.iterdir():
                if file.is_file():
                    dest_file = destination / file.name
                    try:
                        shutil.copy2(file, dest_file)
                        logger.info(f"Copied: {file.name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to copy {file.name}: {e}")

        logger.info("Copying cover images...")
        copy_folder(usb_cover_path, dest_cover_path)

        logger.info("Copying poster images...")
        copy_folder(usb_poster_path, dest_poster_path)

    except Exception as folder_err:
        logger.error(f"❌ Error copying cover/poster folders: {folder_err}")

    db.commit()
    db.close()

    return output

from app.utils.usbpath import find_usb_mount_path
import csv
usb_path = find_usb_mount_path()

def read_db(db_name):
    sql_path = f"{usb_path}/content/database/{db_name}.csv"
    with open(sql_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        output = []
        for row in reader:
            output.append(row)

    return output