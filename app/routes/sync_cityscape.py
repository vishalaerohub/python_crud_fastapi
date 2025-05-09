from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
from app.utils.database import read_db
import os, logging, traceback, shutil
from pathlib import Path
from app.utils.usbpath import find_usb_mount_path


usb_path = find_usb_mount_path()


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/syncCityscape")
def sync_cityscape():
    output = []
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cityscape_data = read_db('city_scapes')
        for item in cityscape_data:
            cityscape_id = item["id"]
            slug = item["city_name"].replace(" ", "-").lower()
            cityscape_data = (
                cityscape_id,
                item["city_name"],
                slug,
                item["thumbnail"],
                item["pdf_path"],
                str(item["status"])
            )

            cursor.execute("""
                INSERT INTO city_scapes (
                    cityscape_id, city_name, cityscape_slug_url, thumbnail, pdf_path, status
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    city_name=VALUES(city_name),
                    cityscape_slug_url=VALUES(cityscape_slug_url),
                    thumbnail=VALUES(thumbnail),
                    pdf_path=VALUES(pdf_path),
                    status=VALUES(status)
            """, cityscape_data)

            # ===== Copy cityscape_pdf and cityscape_thumbnails files =====
            try:
                usb_pdf_path = Path(usb_path)/ "content/cityscape_pdf"
                usb_thumbs_path = Path(usb_path)/ "content/cityscape_thumbnails"
                dest_pdf_path = Path("/home/suhail/Python_Project/python_crud_fastapi/public/cityscape_pdf")
                dest_thumbs_path = Path("/home/suhail/Python_Project/python_crud_fastapi/public/cityscape_thumbnails")

                dest_pdf_path.mkdir(parents=True, exist_ok=True)
                dest_thumbs_path.mkdir(parents=True, exist_ok=True)

                def copy_file(filename: str, src_dir: Path, dest_dir: Path):
                    if filename:
                        source_file = src_dir / os.path.basename(filename)
                        dest_file = dest_dir / os.path.basename(filename)
                        if source_file.exists():
                            shutil.copy2(source_file, dest_file)
                            logger.info(f"Copied: {source_file} → {dest_file}")
                        else:
                            logger.warning(f"File not found: {source_file}")

                copy_file(item["pdf_path"], usb_pdf_path, dest_pdf_path)
                copy_file(item["thumbnail"], usb_thumbs_path, dest_thumbs_path)

            except Exception as copy_err:
                logger.error(f"Error copying cityscape files: {copy_err}")

            logger.info(f"Synced cityscape ID {cityscape_id} - {item['city_name']}")
            output.append({
                "cityscape_id": cityscape_id,
                "message": f"{item['city_name']} synced successfully",
                "status": "true",
                "code": "200"
            })

        db.commit()
    except Exception as e:
        db.rollback()
        logger.critical("❌ DB error while syncing cityscape", exc_info=True)
        raise HTTPException(status_code=500, detail="Error while syncing cityscape")
    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
