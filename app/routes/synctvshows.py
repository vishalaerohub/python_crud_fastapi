from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import os
import traceback
import shutil
import logging
from pathlib import Path
from app.utils.getFileSize import list_files_with_sizes
from app.utils.usbpath import find_usb_mount_path, box_base_path
from app.utils.database import read_db

router = APIRouter()
usb_path = find_usb_mount_path()

# Logging setup
logging.basicConfig(
    filename='file_copy.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_remove(path: str):
    try:
        os.remove(path)
        logger.info(f"Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"File not found (skipping): {path}")
    except Exception as e:
        logger.error(f"❌ Error removing file {path}: {e}")
        traceback.print_exc()


# apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
# HEADERS = {"partner-id": "AEROADVE20240316A377"}

@router.get("/syncTvshows")


# API_URL = apiEndPointBaseUrl + "syncTvshows"
    
    # try:
    #     response = requests.get(API_URL, headers=HEADERS, timeout=10)
    #     response.raise_for_status()
    #     response_data = response.json()
    # except requests.RequestException as e:
    #     logger.error(f"❌ API request failed: {e}")
    #     traceback.print_exc()
    #     raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

    # if not response_data.get("data"):
    #     raise HTTPException(status_code=404, detail="Data is not available")

    # if response_data.get("status") != 1:
    #     return {
    #         "data": "Data not available",
    #         "status": "false",
    #         "code": 404
    #     }

def sync_tv_shows():
    output = []
    db = get_db_connection()

    try:
        cursor = db.cursor()
        tv_data = read_db('tvshows')
        for item in tv_data:
            ad_id = item["ad_id"] if item["ad_id"] not in [None, "", "0"] else None

            if item["is_deleted"] == "1":
                try:
                    shutil.rmtree(os.path.join("public", item["src"]), ignore_errors=True)
                    safe_remove(os.path.join("public", item["p_src"]))
                    safe_remove(os.path.join("public", item["bd_src"]))
                    logger.info(f" Deleted files for TV show ID {item['id']}")
                except Exception as e:
                    logger.warning(f" Error deleting files for TV show ID {item['id']}: {e}")
                    traceback.print_exc()

                cursor.execute("DELETE FROM tvshows WHERE id = %s", (item["id"],))
                logger.info(f" Deleted TV show ID {item['id']} from database")
                continue

            tvshow_data = (
                 item["id"], item["lang"], item["title"], item["display_title"], item["media_type"],
                 item["genre"], item["distributor"], str(item["synopsis"]), item["year"],
                 item["duration"], item["TMDbId"], item["src"], item["p_src"], item["bd_src"],
                 item["rating"], item["highlight"], item["cast"], item["direction"], item["position"],
                 item["start_date"], item["end_date"], ad_id, item["is_deleted"], str(item["status"]),
                 item["type"], item["attached_id"], item["episode_num"]
                )

            try:
                cursor.execute("""
                    INSERT INTO tvshows (
                        id, lang, title, display_title, media_type, genre, distributor, synopsis, year, duration,
                        TMDbId, src, p_src, bd_src, rating, Highlight, cast, direction,
                        position, start_date, end_date, ad_id, is_deleted, status,
                        type, attached_id, episode_num
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        lang=VALUES(lang), title=VALUES(title), display_title=VALUES(display_title),
                        media_type=VALUES(media_type), genre=VALUES(genre), distributor=VALUES(distributor),
                        synopsis=VALUES(synopsis), year=VALUES(year), duration=VALUES(duration),
                        TMDbId=VALUES(TMDbId), src=VALUES(src), p_src=VALUES(p_src), bd_src=VALUES(bd_src),
                        rating=VALUES(rating), Highlight=VALUES(Highlight), cast=VALUES(cast),
                        direction=VALUES(direction), position=VALUES(position),
                        start_date=VALUES(start_date), end_date=VALUES(end_date),
                        ad_id=VALUES(ad_id), is_deleted=VALUES(is_deleted), status=VALUES(status),
                        type=VALUES(type), attached_id=VALUES(attached_id), episode_num=VALUES(episode_num)
                """, tvshow_data)

                exists = ""
                copy = ""
                base_path = os.path.join(f"{usb_path}/content/tvshows")
                source_folder_path = os.path.join(base_path, item["TMDbId"])
                destination_folder_path = os.path.join(f"{box_base_path()}tvshows", item["TMDbId"])

                if os.path.isdir(source_folder_path):
                    # If already exists in box
                    if os.path.isdir(destination_folder_path):
                        source_common = Path(os.path.join(source_folder_path, "common"))
                        dest_common = Path(os.path.join(destination_folder_path, "common"))
                        if source_common.exists() and dest_common.exists():
                            src_files = list_files_with_sizes(source_common)["files"]
                            dst_files = list_files_with_sizes(dest_common)["files"]

                            dst_file_set = {(f["name"], f["size_bytes"]) for f in dst_files}

                            for file in src_files:
                                key = (file["name"], file["size_bytes"])
                                if key not in dst_file_set:
                                    try:
                                        shutil.copy2(source_common / file["name"], dest_common / file["name"])
                                    except Exception as file_err:
                                        logger.warning(f"Failed to copy {file['name']}: {file_err}")
                    else:
                        exists = "Not exists in box."
                        try:
                            shutil.copytree(source_folder_path, destination_folder_path, dirs_exist_ok=True)
                            copy = f"Copied {source_folder_path} to {destination_folder_path}"
                        except Exception as copy_err:
                            copy = f"Failed to copy: {copy_err}"
                else:
                    exists = "Folder does not exist."

                output.append({
                    "tvshow_id": item['id'],
                    "message": f"{item['title']} has been updated",
                    "status": "true",
                    "code": "200",
                    "is_exists": exists,
                    "copied": copy
                })

                logger.info(f"Upserted TV show: {item['title']} (ID: {item['id']})")

            except Exception as e:
                logger.error(f"SQL Error for TV show ID {item['id']}: {e}")
                traceback.print_exc()
                logger.debug("Data causing error: %s", tvshow_data)

        db.commit()

    except Exception as db_error:
        db.rollback()
        logger.critical(" Fatal DB error. Rolled back transaction.")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
