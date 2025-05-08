from fastapi import APIRouter, HTTPException
<<<<<<< HEAD
=======
import logging
import traceback
import requests
>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
from app.db import get_db_connection
from app.utils.getFileSize import list_files_with_sizes
from app.utils.dateParse import parse_date
from app.utils.usbpath import find_usb_mount_path
from app.utils.database import read_db

<<<<<<< HEAD
import os
import traceback
import logging
import shutil
import requests

# Create router instance
router = APIRouter()

usb_path = find_usb_mount_path()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL and headers (adjust as needed)
#apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
#HEADERS = {"partner-id": "AEROADVE20240316A377"}


@router.get("/sync-music-playlists")
def sync_music_playlists():
    #API_URL = apiEndPointBaseUrl + "syncMusicsPlaylist"
    
    #try:
       # response = requests.get(API_URL, headers=HEADERS, timeout=10)
       # response.raise_for_status()
       # response_data = response.json()
   # except requests.RequestException as e:
       # logger.error(f"❌ API request failed: {e}")
       # traceback.print_exc()
      #  raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

   # if not response_data.get("data"):
       # raise HTTPException(status_code=404, detail="Data is not available")
=======


# USB mount path
usb_path = find_usb_mount_path()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


#apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"
#HEADERS = {"partner-id": "AEROADVE20240316A377"} 

# Create the router
router = APIRouter()

@router.get("/sync-music-playlists")
def syncMusicsPlaylist():
    #API_URL = apiEndPointBaseUrl + "syncMusicsPlaylist"
    
    #try:
        # Make the API request
       # response = requests.get(API_URL, headers=HEADERS, timeout=10)
       # response.raise_for_status()
       # response_data = response.json()
    #except requests.RequestException as e:
       # logger.error(f"❌ API request failed: {e}")
       # logger.error(traceback.format_exc())  
       # raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")
    
    #if not response_data.get("data"):
        #raise HTTPException(status_code=404, detail="Data is not available")
>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
    
    playlists = read_db ('playlists')
    db = get_db_connection()
    cursor = db.cursor()
    output = []
    
<<<<<<< HEAD
    
=======
>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
    for playlist in playlists:
        playlist_id = playlist["id"]
        
        try:
<<<<<<< HEAD
            created_at = parse_date(playlist['createdAt'])
            updated_at = parse_date(playlist['updatedAt'])
            status = str(playlist["status"])
            
            playlist_data = (
                playlist["id"],
                playlist["id"],
=======
            # Parse date fields
            created_at = parse_date(playlist['createdAt'])
            updated_at = parse_date(playlist['updatedAt'])
            status = str(playlist["status"])

            # Prepare data for insertion
            playlist_data = (
                playlist["id"],
                playlist["id"],  
>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
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
            
<<<<<<< HEAD
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
            
=======
            # Insert or update playlist data in DB
            cursor.execute("""
                INSERT INTO playlists (id, id2, title, lang, description, genres, cover_path, Highlight, active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                id=VALUES(id), id2=VALUES(id), title=VALUES(title), lang=VALUES(lang),
                description=VALUES(description), genres=VALUES(genres), cover_path=VALUES(cover_path),
                Highlight=VALUES(Highlight), active=VALUES(active), created_at=VALUES(created_at),
                updated_at=VALUES(updated_at)
            """, playlist_data)

>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
            output.append({
                "song_id": playlist['id'],
                "message": f"'{playlist['title']}' has been synced.",
                "status": "true",
                "code": "200"
            })
<<<<<<< HEAD
             
        except Exception as e:
            traceback.print_exc()
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error syncing song ID {playlist_id}: {str(e)}")
    
=======
            
        except Exception as e:
            logger.error(f"Error syncing playlist ID {playlist_id}: {str(e)}")
            logger.error(traceback.format_exc())
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error syncing playlist ID {playlist_id}: {str(e)}")
    
    # Commit and close the database connection
>>>>>>> acc3511 (Added sync_music_playlists route for read offline CSV content as offline database)
    db.commit()
    db.close()

    return output
