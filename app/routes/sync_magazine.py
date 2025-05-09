from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
from app.utils.database import read_db
from app.utils.usbpath import find_usb_mount_path,box_base_path
from pathlib import Path
import shutil
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/syncMagazine")
def sync_magazine():
    output = []
    usb_path = find_usb_mount_path()
    if not usb_path:
        logger.error("❌ USB path not found.")
        raise HTTPException(status_code=400, detail="USB path not found")

    db = get_db_connection()

    try:
        cursor = db.cursor()
        magazine_data = read_db('magazines')


        for item in magazine_data:
            if int(item["status"]) == 1:

                magazine_data = (
                    item["id"],
                    item["name"],
                    item["language"],
                    item["path"],
                    item["thumbnail"],
                    item["status"],
                    item["magazine_date"],
                    item["size"],
                    item["file_format"]
                )

                cursor.execute("""
                 INSERT INTO magazines (
                     magazine_id, name, language, path, thumbnail, status, magazine_date, size, file_format
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                   name=VALUES(name),
                   language=VALUES(language),
                   path=VALUES(path),
                   thumbnail=VALUES(thumbnail),
                   status=VALUES(status),
                   magazine_date=VALUES(magazine_date),
                   size=VALUES(size),
                   file_format=VALUES(file_format)
                """, magazine_data) 

                output.append({
                    "magazine_id": item["id"],
                    "message": f"{item['name']} synced successfully"
                })

        # ===== Copy magazines and magazine_thumbnails folders =====
        try:
            usb_magazines_path = Path(usb_path) / "content/magazines"
            usb_magazine_thumbnails_path = Path(usb_path) / "content/magazine_thumbnails"
            dest_magazines_path = Path(f"{box_base_path()}magazines")
            dest_magazine_thumbnails_path = Path(f"{box_base_path()}magazine_thumbnails")

            dest_magazines_path.mkdir(parents=True, exist_ok=True)
            dest_magazine_thumbnails_path.mkdir(parents=True, exist_ok=True)

            def copy_folder(source: Path, destination: Path):
                if not source.exists():
                    logger.warning(f"Source folder does not exist: {source}")
                    return
                for file in source.iterdir():
                    if file.is_file():
                        dest_file = destination / file.name
                        try:
                            shutil.copy2(file, dest_file)
                            logger.info(f"Copied: {file.name}")
                        except Exception as e:
                            logger.error(f" Failed to copy {file.name}: {e}")

            logger.info("Copying magazine files...")
            copy_folder(usb_magazines_path, dest_magazines_path)

            logger.info("Copying thumbnail files...")
            copy_folder(usb_magazine_thumbnails_path, dest_magazine_thumbnails_path)

        except Exception as folder_err:
            logger.error(f" Error copying folders: {folder_err}")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error("DB Error during magazine sync", exc_info=True)
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
