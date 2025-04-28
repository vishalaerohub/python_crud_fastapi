from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, traceback, shutil, logging, json
from app.utils.dateParse import parse_date
from app.utils.downloader import downloadAndSaveFile
from fastapi.responses import JSONResponse

import subprocess
import re
from app.utils.usbpath import find_usb_mount_path

usb_path = find_usb_mount_path()

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


@router.get("/syncAdvertisement")
def syncAdvertisement():
    API_URL = apiEndPointBaseUrl + "syncAdvertisement"
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
    
    # return response_data["data"]
    try:
        cursor = db.cursor()
        
        for item in response_data["data"]:
            created_at = parse_date(item['createdAt'])
            updated_at = parse_date(item['updatedAt'])
            ad_id = item["id"]
            url = item['url']
            
            if item['advertise_type'] == 'Carousel':
                downloadAndSaveFile(item['desktop_url'], 'desktop_carousels')
                
                downloadAndSaveFile(item['url'], 'mobile_carousels')
            else:
                downloadAndSaveFile(url, 'videos')
                
            ad_data = (
                item.get("id"),
                item.get('name') or '',
                item.get('advertise_type') or '',
                item.get('url') or '',
                item.get('desktop_url') or '',
                item.get('ad_clicksection') or '',
                item.get('ad_clickid') or '',
                str(item.get('status') or '0'),
                item.get('size') or '',
                item.get('content_type') or '',
                item.get('is_skip') or 0,
                item.get('skiptimein_second') or 0,
                item.get('file_format') or '',
                created_at,
                updated_at
            )
            try:
                cursor.execute("""
                    INSERT INTO advertisements (
                        adv_id,name, advertise_type, url, desktop_url, ad_clicksection, ad_clickid, status, size, content_type, is_skip, skip_timein_second, file_format, created_at, updated_at
                    ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name=VALUES(name),
                        advertise_type=VALUES(advertise_type),
                        url=VALUES(url),
                        desktop_url=VALUES(desktop_url),
                        ad_clicksection=VALUES(ad_clicksection),
                        ad_clickid=VALUES(ad_clickid),
                        status=VALUES(status),
                        size=VALUES(size),
                        content_type=VALUES(content_type),
                        is_skip=VALUES(is_skip),
                        skip_timein_second=VALUES(skip_timein_second),
                        file_format=VALUES(file_format),
                        created_at=VALUES(created_at),
                        updated_at=VALUES(updated_at)
                """, ad_data)
                
                output.append({
                    "ad_id" : item['id'],
                    "message": f"Ad '{item['name']}' synced"
                })
            except Exception as db_err:
                logger.error(f"❌ SQL error for ad ID {ad_id}: {db_err}")
                traceback.print_exc()
                output.append({
                    "ad_id": ad_id,
                    "message": f"Failed to sync ad '{item['name']}'",
                    "status": "true"
                })
                
        db.commit()
    except Exception as e:
        db.rollback()
        logger.critical("❌ DB error during ad sync", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync advertisements")
    finally:
        db.close()
        
    return output   

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
    # return playlists
    db = get_db_connection()
    cursor = db.cursor()
    output = []
    
    for playlist in playlists:
        playlist_id = playlist["id"]
        
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
                INSERT INTO playlists (id, id2, title, lang, description, genres, cover_path, Highlight, active, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                
                ON DUPLICATE KEY UPDATE
                id=VALUES(id),id2=VALUES(id),title=VALUES(title),lang=VALUES(lang),description=VALUES(description),genres=VALUES(genres),cover_path=VALUES(cover_path),Highlight=VALUES(Highlight),active=VALUES(active),created_at=VALUES(created_at),updated_at=VALUES(updated_at)
            """, playlist_data)
            
            output.append({
                    "song_id": playlist['id'],
                    "message": f"'{playlist['title']}' has been synced.",
                    "status": "true",
                    "code": "200"
            })
             
        except Exception as e:
            traceback.print_exc()
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error syncing song ID {playlist_id}: {str(e)}")
            
        
    db.commit()
    db.close()

    return output
        
# @router.get("/sync-music")
# def syncMagazine_router():
#     API_URL = apiEndPointBaseUrl + "syncMusics"
#     try:
#         response = requests.get(API_URL, headers=HEADERS, timeout=10)
#         response.raise_for_status()
#         response_data = response.json()
#     except requests.RequestException as e:
#         logger.error(f"❌ API request failed: {e}")
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

#     if not response_data.get("data"):
#         raise HTTPException(status_code=404, detail="Data is not available")
    
#     songs = response_data["data"]
#     db = get_db_connection()
#     cursor = db.cursor()
#     output = []

#     for song in songs:
#         song_id = song["id"]
#         is_deleted = song["is_deleted"]

#         try:
#             if is_deleted == 1:
#                 # Delete files
#                 song_path = os.path.join("public", song["song_path"].lstrip("/"))
#                 cover_path = os.path.join("public", song["cover_path"].lstrip("/"))
#                 if os.path.exists(song_path):
#                     os.remove(song_path)
#                 if os.path.exists(cover_path):
#                     os.remove(cover_path)

#                 # Delete DB record
#                 cursor.execute("DELETE FROM songs WHERE id = %s", (song_id,))
#             else:
#                 # Convert datetime strings to MySQL format
#                 created_at = parse_date(song['createdAt'])
#                 updated_at = parse_date(song['updatedAt'])

#                 cursor.execute("""
#                     INSERT INTO songs (
#                         id, partner_id, title, genres, album, year, category, artist, status,
#                         song_path, cover_path, playlist_id, is_deleted, position,
#                         start_date, end_date, created_at, updated_at
#                     ) VALUES (
#                         %s, %s, %s, %s, %s, %s, %s, %s, %s,
#                         %s, %s, %s, %s, %s,
#                         %s, %s, %s, %s
#                     )
#                     # ON DUPLICATE KEY UPDATE
#                     #     partner_id=VALUES(partner_id), title=VALUES(title), genres=VALUES(genres),
#                     #     album=VALUES(album), year=VALUES(year), category=VALUES(category),
#                     #     artist=VALUES(artist), status=VALUES(status), song_path=VALUES(song_path),
#                     #     cover_path=VALUES(cover_path), playlist_id=VALUES(playlist_id), is_deleted=VALUES(is_deleted),
#                     #     position=VALUES(position), start_date=VALUES(start_date), end_date=VALUES(end_date),
#                     #     created_at=VALUES(created_at), updated_at=VALUES(updated_at)
#                 """, (
#                     song_id, song["partner_id"], song["title"], song["genres"], song["album"], song["year"],
#                     song["category"], song["artist"], str(song["status"]), song["song_path"], song["cover_path"],
#                     song["playlist_id"], is_deleted, song["position"],
#                     song["start_date"], song["end_date"], created_at, updated_at
#                 ))
#                 output.append({
#                     "song_id": song['id'],
#                     "message": f"'{song['title']}' has been synced.",
#                     "status": "true",
#                     "code": "200"
#                 })

#         except Exception as e:
#             traceback.print_exc()
#             db.rollback()
#             raise HTTPException(status_code=500, detail=f"Error syncing song ID {song_id}: {str(e)}")

#     db.commit()
#     db.close()

#     return output

@router.get('/syncAnalytics')
def syncAnalytics():
    batch_size = 100
    total_records_processed = 0
    total_batches_processed = 0
    successful_batches = 0
    failed_batches = 0
    
    # API_URL = apiEndPointBaseUrl + "saveanalytics"
    API_URL = "https://ifeanalytics-api.aerohub.aero/api/device/saveanalytics"
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # while True:
    try:
        cursor.execute(f"""
            SELECT 
                id, name, event, subject, ip, description, created_at, 
                content_id, user_id, source_city AS source, destination_city AS destination
            FROM analytics 
            WHERE status = '0'
            ORDER BY id
            LIMIT {batch_size}
        """)
        analytics_res = cursor.fetchall()
        
        if not analytics_res:
            return {"message": "No new analytics for you"}

        # ADD DEVICE ID TO EACH RECORD
        for record in analytics_res:
            record["device_id"] = get_device_id()
            
            # if isinstance(record.get("created_at"), datetime):
            record["created_at"] = record["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        
        # return analytics_res
        
        # send to external api
        response = requests.post(API_URL, headers=HEADERS, json=analytics_res, timeout=100)
        if response.status_code == 200:
            successful_batches += 1
            total_batches_processed += 1
            total_records_processed += len(analytics_res)

            # Optionally mark records as synced (status = 1)
            ids = tuple(record["id"] for record in analytics_res)
            format_strings = ','.join(['%s'] * len(ids))
            cursor.execute(f"UPDATE analytics SET status = '1' WHERE id IN ({format_strings})", ids)
            db.commit()

            return {
                "message": "Batch synced successfully.",
                "status_code": response.status_code,
                "records_synced": len(analytics_res)
            }
        else:
            failed_batches += 1
            db.rollback()
            return {
                "message": "Failed to sync batch.",
                "status_code": response.status_code,
                "details": response.text
            }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        db.close()
        
    
    
def get_device_id():
    try:
        # Try to get MAC from interfaces starting with enp
        result = subprocess.run("ip link show | grep -A1 enp | awk '/link\\/ether/ {print $2}'", 
                                shell=True, capture_output=True, text=True)
        mac_address = re.sub(r'\s+', '', result.stdout)

        if not mac_address:
            # Try alternative way
            result = subprocess.run("ip -o link show | awk -F ' ' '/enp/ {print $17}'", 
                                    shell=True, capture_output=True, text=True)
            mac_address = re.sub(r'\s+', '', result.stdout)

        if not mac_address:
            # Fallback for any link/ether
            result = subprocess.run("ip -o link show | awk -F ' ' '/link\\/ether/ {print $17}'", 
                                    shell=True, capture_output=True, text=True)
            mac_address = re.sub(r'\s+', '', result.stdout)

        return mac_address
    except Exception as e:
        print("Error getting MAC address:", str(e))
        return None
    


# @router.get("/usb-path")
# def get_usb_path():
#     usb_path = find_usb_mount_path()
#     return usb_path
#     if usb_path:
#         base_path = os.path.join(usb_path)
#         return {"status": "success", "base_path": base_path}
#     else:
#         return {"status": "error", "message": "No USB drive detected"}
    
    