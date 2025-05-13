from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import requests, os, traceback, shutil, logging, json
from app.utils.dateParse import parse_date
from app.utils.downloader import downloadAndSaveFile
from app.utils.database import read_db
from fastapi.responses import JSONResponse

import subprocess
import re
from app.utils.usbpath import find_usb_mount_path, box_base_path
from pathlib import Path

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

@router.get('/get-usb')
def get_usb():
    return {
        "data": usb_path
    }

@router.get("/syncAdvertisement")
def syncAdvertisement():
    output = []
    db = get_db_connection()
    
    # return response_data["data"]
    try:
        cursor = db.cursor()
        advertisements = read_db('advertisements')
        
        # return advertisements
        base_path = f"{usb_path}/content/desktop_carousels/"
        for item in advertisements:
            created_at = item['created_at']
            updated_at = item['updated_at']
            ad_id = item["id"]
            url = item['url']
            
            if item['advertise_type'] == 'Carousel':
                # start download file from pendrive
                desktop_url = os.path.basename(item['desktop_url'])
                url = os.path.basename(item['url'])
                
                desktop_source_folder = Path(base_path+ desktop_url)
                desktop_destination_folder = Path(f"{box_base_path()}/desktop_carousels")
                
                desktop_destination_folder.mkdir(parents=True, exist_ok=True)
                desktop_final_destination = desktop_destination_folder / desktop_source_folder.name
                
                shutil.copy2(desktop_source_folder, desktop_final_destination)
                
                # downloadAndSaveFile(item['desktop_url'], 'desktop_carousels')
                
                mobile_source_folder = Path(base_path+ desktop_url)
                mobile_destination_folder = Path(f"{box_base_path()}/mobile_carousels")
                
                mobile_destination_folder.mkdir(parents=True, exist_ok=True)
                mobile_final_destination = mobile_destination_folder / mobile_source_folder.name
                
                shutil.copy2(mobile_source_folder, mobile_final_destination)
                
                # downloadAndSaveFile(item['url'], 'mobile_carousels')
            else:
                video_source_folder = Path(base_path+ url)
                video_destination_folder = Path(f"{box_base_path()}/videos")
                
                video_destination_folder.mkdir(parents=True, exist_ok=True)
                video_final_destination = video_destination_folder / video_source_folder.name
                
                shutil.copy2(mobile_source_folder, video_final_destination)
                # downloadAndSaveFile(url, 'videos')
                
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
    try:
        while True:
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
                break

            # ADD DEVICE ID TO EACH RECORD
            for record in analytics_res:
                record["device_id"] = get_device_id()
                record["created_at"] = record["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            
            try:
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

                    
                else:
                    failed_batches += 1
                    db.rollback()
                    print(f"Failed to sync batch. Status: {response.status_code}")
            except Exception as e:
                failed_batches += 1
                db.rollback()
                print(f"Error sending batch: {e}")
            return {
                "message": "Sync process completed.",
                "total_records_processed": total_records_processed,
                "total_batches_processed": total_batches_processed,
                "successful_batches": successful_batches,
                "failed_batches": failed_batches
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
    
    