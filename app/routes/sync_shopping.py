from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import os, logging, traceback, shutil
from app.utils.database import read_db
from app.utils.usbpath import find_usb_mount_path
from pathlib import Path

usb_path = find_usb_mount_path()


# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def safe_remove(path: str):
    try:
        os.remove(path)
        logger.info(f"Removed file: {path}")
    except FileNotFoundError:
        logger.warning(f"File not found (skipping): {path}")
    except Exception as e:
        logger.error(f"Error removing file {path}: {e}")
        traceback.print_exc()

@router.get("/sync-shopping")
async def sync_shopping():
    output = []
    db = get_db_connection()

    try:
        cursor = db.cursor()

        for item in read_db('shoppinginfo'):

        
            shopping_data = (
                item["id"],
                item["name"],
                os.path.basename(item["path"]), 
            )

            try:
                cursor.execute("""
                    INSERT INTO shoppinginfo (id, name, path)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name=VALUES(name),
                        path=VALUES(path)
                """, shopping_data)

                output.append({
                    "shopping_id": item['id'],
                    "message": f"'{item['name']}' has been updated",
                    "status": "true",
                    "code": "200"
                })
                logger.info(f"Upserted shopping info: {item['name']} (ID: {item['id']})")

            except Exception as e:
                logger.error(f"❌SQL Error for shopping item ID {item['id']}: {e}")
                traceback.print_exc()

          # ===== Copy File Code =====

        try:
            
            usb_shopping_path = Path(usb_path) / "content/shopping"
            dest_shopping_path = Path("/home/suhail/Python_Project/python_crud_fastapi/public/shopping")

            dest_shopping_path.mkdir(parents=True, exist_ok=True)

            def copy_folder(source: Path, destination: Path):
                if not source.exists():
                    logger.warning(f"Source folder does not exist: {source}")
                    return
                for file in source.iterdir():
                    if file.is_file():
                        dest_file = destination / file.name
                        try:
                            shutil.copy2(file, dest_file)
                            logger.info(f" Copied: {file.name}")
                        except Exception as e:
                            logger.error(f"Failed to copy {file.name}: {e}")

            logger.info("Copying shopping files...")
            copy_folder(usb_shopping_path, dest_shopping_path)

        except Exception as folder_err:
            logger.error(f"Error copying shopping folder: {folder_err}")
        # End: Copy block

        db.commit()

    except Exception as db_error:
        db.rollback()
        logger.critical("Fatal DB error. Rolled back transaction.")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database operation failed")

    finally:
        db.close()
        logger.info("🔒 Database connection closed.")

    return output
