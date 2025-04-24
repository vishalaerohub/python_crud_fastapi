from fastapi import APIRouter, HTTPException
import requests
import traceback
from utils import get_db_connection, parse_date
import os, shutil, logging
from pathlib import Path
from app.utils.getFileSize import list_files_with_sizes

router = APIRouter()
logger = logging.getLogger(__name__)

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"  
HEADERS = {"partner-id": "AEROADVE20240316A377"}

@router.get("/sync-music-playlists")
def syncMusicsPlaylist():
    API_URL = apiEndPointBaseUrl + "syncMusicsPlaylist"
    
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
    
    playlists = response_data["data"]
    db = get_db_connection()
    cursor = db.cursor()
    output = []

    for playlist in playlists:
        playlist_id = playlist["id"]
        copied = ""
        exists = ""

        try:
            created_at = parse_date(playlist['createdAt'])
            updated_at = parse_date(playlist['updatedAt'])
            status = str(playlist["status"])
            
            playlist_data = (
                playlist["id"],
                playlist["id"],
                playlist["title"],
                playlist["lang"],
                playlist["description"],
                playlist["genres"],
                playlist["cover_path"],
                playlist["Highlight"],
                status,
                created_at,
                updated_at,
            )
            
            cursor.execute("""
                INSERT INTO playlists 
                (id, id2, title, lang, description, genres, cover_path, Highlight, active, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id=VALUES(id),
                    id2=VALUES(id2),
                    title=VALUES(title),
                    lang=VALUES(lang),
                    description=VALUES(description),
                    genres=VALUES(genres),
                    cover_path=VALUES(cover_path),
                    Highlight=VALUES(Highlight),
                    active=VALUES(active),
                    created_at=VALUES(created_at),
                    updated_at=VALUES(updated_at)
            """, playlist_data)

            # ====== START: Copy logic ======
            base_path = "/media/suhail/891D-C373/content/Songs"
            if os.path.isdir(base_path + str(playlist["id"])):
                source_folder = Path(base_path + str(playlist["id"]))
                destination_folder = Path("/home/suhail/Python_Project/python_crud_fastapi/public/Songs")
                destination_folder.mkdir(parents=True, exist_ok=True)
                final_destination = destination_folder / source_folder.name

                if os.path.isdir(final_destination):
                    source_common_folder = source_folder / 'common'
                    destination_common_folder = final_destination / 'common'

                    if source_common_folder.exists() and destination_common_folder.exists():
                        src_info = list_files_with_sizes(source_common_folder)
                        dst_info = list_files_with_sizes(destination_common_folder)

                        if src_info["total_files"] == dst_info["total_files"]:
                            dst_files_set = {(f["name"], f["size_bytes"]) for f in dst_info["files"]}
                            for f in src_info["files"]:
                                key = (f["name"], f["size_bytes"])
                                if key not in dst_files_set:
                                    shutil.copy2(source_common_folder / f["name"], destination_common_folder / f["name"])
                                    copied = f"📁 Copied missing file: {f['name']}"
                        else:
                            shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                            copied = f" Full folder copied from {source_folder} to {final_destination}"
                    else:
                        copied = "Either source or destination common folder missing"
                else:
                    shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                    copied = f"✅ Copied new folder: {source_folder.name}"
            else:
                exists = "⛔ Folder does not exist in USB"
            # ====== END: Copy logic ======

            output.append({
                "playlist_id": playlist['id'],
                "message": f"'{playlist['title']}' has been synced.",
                "status": "true",
                "code": "200",
                "is_exists": exists,
                "copied": copied
            })

        except Exception as e:
            logger.error(f"❌ Failed to sync playlist ID {playlist_id}: {e}")
            traceback.print_exc()
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error syncing playlist ID {playlist_id}: {str(e)}")

    db.commit()
    db.close()

    return {"message": "Music playlists synced successfully", "synced_playlists": output}
