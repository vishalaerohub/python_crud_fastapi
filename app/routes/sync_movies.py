# import httpx
from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, traceback, shutil, logging, json
from app.utils.getFileSize import list_files_with_sizes, list_folders_with_sizes
# from app.utils.downloader import downloadAndSaveFile
# from fastapi.responses import JSONResponse
from pathlib import Path
import logging
from app.utils.usbpath import find_usb_mount_path, box_base_path

usb_path = find_usb_mount_path()

router = APIRouter()

# Configure basic logging
logging.basicConfig(
    filename='file_copy.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
    
)
logger = logging.getLogger(__name__)

def safe_remove(path: str):
    try:
        os.remove(path)
        logger.info(f"✅ Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"⚠️ File not found (skipping): {path}")
    except Exception as e:
        logger.error(f"❌ Error removing file {path}: {e}")
        traceback.print_exc()


apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
HEADERS = {"partner-id": "AEROADVE20240316A377"}

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
        return response_data["data"]
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
                logging.info(f"❌ Deleted movie ID {item['id']} from database")

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
                    exists = ''
                    copy = ""
                    
                    # in case of our matching case:
                    base_path = f"{usb_path}/content/moviesMedia/"
                    if os.path.isdir(base_path + item['TMDbId']): #its cheking from pendrive
                        
                        source_folder = Path(base_path + item['TMDbId']) # this is Pendrive path
                        destination_folder = Path(f"{box_base_path()}moviesMedia") # this is box path my my movie will be going to copy
                        
                        # Make sure the destination directory exists or create it
                        destination_folder.mkdir(parents=True, exist_ok=True)

                        # Set the full destination path (including copied folder name)
                        final_destination = destination_folder / source_folder.name
                        
                        # now check folder existance in box or code repo
                        if os.path.isdir(f"/home/vishal/aerohub/python_crud_fastapi/public/moviesMedia/{item['TMDbId']}"):
                            # now check each file from movies folder and their chunks file based on counting and size
                            source_common_folder      = Path(source_folder/ 'common')
                            destination_common_folder = Path(destination_folder/ item['TMDbId']/'common')
                            
                            
                            
                            if source_common_folder.exists() and source_common_folder.is_dir() and destination_common_folder.exists() and destination_common_folder.is_dir():
                                get_folder_files_details_source      = list_files_with_sizes(source_common_folder)
                                get_folder_files_details_destination = list_files_with_sizes(destination_common_folder)
                                # return get_folder_files_details_source
                                
                                source_total_files = get_folder_files_details_source['total_files']
                                destination_total_files = get_folder_files_details_destination['total_files']
                                
                                
                                # return destination_total_files
                                
                                # print(f"source total file {source_total_files}")
                                if source_total_files == destination_total_files:
                                    # copy = f"{item['TMDbId']} is fully fulfilled"
                                    src_files = get_folder_files_details_source["files"]
                                    des_files = get_folder_files_details_destination["files"]
                                    
                                    des_file_set = {(f["name"], f["size_bytes"]) for f in des_files}
                                    
                                    for file in src_files:
                                        key = (file["name"], file["size_bytes"])
                                        if key not in des_file_set:
                                            src_path  = os.path.join(source_common_folder, file["name"])
                                            dest_path = os.path.join(destination_common_folder, file["name"])
                                            
                                            print(f"Copying {file['name']} from source to destination...")
                                            shutil.copy2(src_path, dest_path)
                                            # return file['size_bytes'] # next work start from here....
                                    
                                else:
                                    # return "kuchh to gadbad hai daya!"
                                    shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                                    copy = f"kuchh Copied '{source_folder}' to '{final_destination}'"
                            else:
                                exists =  "No its not exists in movie folder"
                        else:
                            exists = "Not exists in box."

                            if source_folder.exists() and source_folder.is_dir():
                                shutil.copytree(source_folder, final_destination, dirs_exist_ok=True)
                                copy  = f"not exists Copied '{source_folder}' to '{final_destination}'"
                            else:
                                copy = "Source folder does not exist or is not a directory."
                        
                    else:
                        exists = "Folder does not exist."
                        

                    output.append({
                        "movie_id": item['id'],
                        "message": f"{item['title']} has been updated",
                        "status": "true",
                        "code": "200",
                        "is_exists": exists,
                        "copied": copy
                    })
                    logger.info(f"✅ Upserted movie: {item['title']} (ID: {item['id']})")

                except Exception as e:
                    logger.error(f"X SQL Error for movie ID {item['id']}: {e}")
                    traceback.print_exc()
                    logger.debug("Data causing error: %s", movie_data)

        db.commit()
    except Exception as db_error:
        db.rollback()
        logger.critical("X Fatal DB error. Rolled back transaction.")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output


