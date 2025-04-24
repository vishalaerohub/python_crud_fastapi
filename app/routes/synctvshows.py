import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import requests
from app.db import get_db_connection
from app.utils.getFileSize import list_files_with_sizes

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"

def check_folder_existence(folder_path: str):
    """Check if the folder exists and is a directory."""
    folder_path = Path(folder_path)
    print(f"Checking if the folder exists: {folder_path}")
    if folder_path.exists() and folder_path.is_dir():
        print(f"Folder exists: {folder_path}")
        return True
    else:
        print(f"Folder does not exist: {folder_path}")
        return False

@router.get("/syncTvshows")
def sync_tv_shows():
    API_URL = apiEndPointBaseUrl + "syncTvshows"
    HEADERS = {"partner-id": "AEROADVE20240316A377"}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching API: {e}")

    if not response_data.get("data"):
        return JSONResponse(status_code=404, content={"status": False, "message": "No data available"})

    print("✅ API Fetched:", len(response_data["data"]))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    output = []

    try:
        # return response_data["data"]
        for item in response_data["data"]:
            tvshow_id = item.get("id")

            if item.get("is_deleted") == 1:
                # Delete associated files
                for path in [item.get("src"), item.get("p_src"), item.get("bd_src")]:
                    if not path:
                        continue
                    file_path = os.path.join("public", path.strip("/"))
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path, ignore_errors=True)
                        elif os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as file_error:
                        print(f"⚠️ Error deleting file {file_path}: {file_error}")

                # Delete from database
                cursor.execute("DELETE FROM tvshows WHERE id = %s", (tvshow_id,))
                db.commit()
                output.append({"status": 200, "message": "Tvshow deleted", "id": tvshow_id})

            else:
                ad_id = item.get("ad_id") if item.get("ad_id", 0) > 0 else None

                tv_data = (
                    tvshow_id, item.get("lang"), item.get("title"), item.get("display_title"), item.get("media_type"), item.get("genre"),
                    item.get("distributor"), item.get("synopsis"), item.get("year"), item.get("duration"),
                    item.get("TMDbId"), item.get("src"), item.get("p_src"), item.get("bd_src"),
                    item.get("rating"), item.get("Highlight"), item.get("cast"), item.get("direction"),
                    item.get("position"), item.get("start_date"), item.get("end_date"), ad_id,
                    item.get("is_deleted"), str(item.get("status")), item.get("type"),
                    item.get("attached_id"), item.get("episode_num")
                )

                cursor.execute("""
                    INSERT INTO tvshows (
                        lang, title, media_type, genre, distributor, synopsis, year, duration,
                        TMDbId, src, p_src, bd_src, rating, highlight, cast, direction,
                        position, start_date, end_date, ad_id, is_deleted, status, type,
                        attached_id, episode_num
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        lang=VALUES(lang), title=VALUES(title), display_title=VALUES(display_title), media_type=VALUES(media_type),
                        genre=VALUES(genre), distributor=VALUES(distributor), synopsis=VALUES(synopsis),
                        year=VALUES(year), duration=VALUES(duration), TMDbId=VALUES(TMDbId),
                        src=VALUES(src), p_src=VALUES(p_src), bd_src=VALUES(bd_src), rating=VALUES(rating),
                        highlight=VALUES(highlight), cast=VALUES(cast), direction=VALUES(direction),
                        position=VALUES(position), start_date=VALUES(start_date), end_date=VALUES(end_date),
                        ad_id=VALUES(ad_id), is_deleted=VALUES(is_deleted), status=VALUES(status),
                        type=VALUES(type), attached_id=VALUES(attached_id), episode_num=VALUES(episode_num)
                """, tv_data)

                # === Copying logic ===
                exists = ''
                copy = ''

                base_path = "/media/suhail/891D-C373/content/tvshows"
                if check_folder_existence(base_path + item['TMDbId']): # Checking in Pendrive
                    source_folder = Path(base_path + item['TMDbId'])  # Pendrive path
                    destination_folder = Path(f"/home/suhail/Python_Project/python_crud_fastapi/public/tvshows")  # Box path
                    
                    destination_folder.mkdir(parents=True, exist_ok=True)
                    final_destination = destination_folder / source_folder.name

                    if check_folder_existence(f"/home/suhail/Python_Project/python_crud_fastapi/public/tvshows{item['TMDbId']}"):
                        source_common_folder = Path(source_folder / 'common')
                        destination_common_folder = Path(destination_folder / item['TMDbId'] / 'common')

                        if source_common_folder.exists() and source_common_folder.is_dir() and destination_common_folder.exists() and destination_common_folder.is_dir():
                            source_files = list_files_with_sizes(source_common_folder)['files']
                            destination_files = list_files_with_sizes(destination_common_folder)['files']
                            src_files_set = {(f["name"], f["size_bytes"]) for f in source_files}
                            des_files_set = {(f["name"], f["size_bytes"]) for f in destination_files}
                            
                            for file in source_files:
                                if (file["name"], file["size_bytes"]) not in des_files_set:
                                    src_path = os.path.join(source_common_folder, file["name"])
                                    dest_path = os.path.join(destination_common_folder, file["name"])
                                    print(f"Copying {file['name']} from source to destination...")
                                    shutil.copy2(src_path, dest_path)
                            copy = "Some files copied."
                        else:
                            shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                            copy = f"Copied '{source_folder}' to '{final_destination}'"
                    else:
                        exists = "Not exists in box."
                        if source_folder.exists() and source_folder.is_dir():
                            shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                            copy = f"Copied '{source_folder}' to '{final_destination}'"
                        else:
                            copy = "Source folder does not exist or is not a directory."
                else:
                    exists = "Folder does not exist in Pendrive."

                output.append({
                    "tvshow_id": item['id'],
                    "message": f"{item['title']} has been updated",
                    "status": "true",
                    "code": "200",
                    "is_exists": exists,
                    "copied": copy
                })
                print(f"✅ Upserted movie: {item['title']} (ID: {item['id']})")

        db.commit()
        output.append({"status": 200, "message": "Tvshow synced and media copied", "id": tvshow_id})

    except Exception as db_error:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {db_error}")
    finally:
        db.close()

    return {
        "status": True,
        "message": "Sync complete",
        "results": output
    }
