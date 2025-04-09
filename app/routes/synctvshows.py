from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import mysql.connector
import requests
import os
import shutil

router = APIRouter()

apiEndPointBaseUrl = "https://ifeanalytics-api.aerohub.aero/api/deviceContent/"

@router.get("/syncTvshows")
def syncTvshows():
    API_URL = apiEndPointBaseUrl + "syncTvshows"
    HEADERS = {"partner-id": "AEROADVE20240316A377"}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching API: {e}")

    if not response_data.get("data"):
        return {"status": False, "message": "No data available", "code": 404}

    print("✅ API Fetched:", len(response_data["data"]))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    output = []

    try:
        for item in response_data["data"]:
            if item["is_deleted"] == 1:
                # Delete files
                for path in [item["src"], item["p_src"], item["bd_src"]]:
                    file_path = os.path.join("public", path.strip("/"))
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                    elif os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass

                # Delete from database
                cursor.execute("DELETE FROM tvshows WHERE id = %s", (item["id"],))
                db.commit()

            else:
                ad_id = item["ad_id"] if item.get("ad_id", 0) > 0 else None

                cursor.execute("SELECT id FROM tvshows WHERE id = %s", (item["id"],))
                exists = cursor.fetchone()

                # Ensure all required fields exist using .get()
                tv_data = (
                    item.get("lang"), item.get("title"), item.get("media_type"), item.get("genre"), item.get("distributor"),
                    item.get("synopsis"), item.get("year"), item.get("duration"), item.get("TMDbId"),
                    item.get("src"), item.get("p_src"), item.get("bd_src"), item.get("rating"),
                    item.get("Highlight"), item.get("cast"), item.get("direction"), item.get("position"),
                    item.get("start_date"), item.get("end_date"), ad_id, item.get("is_deleted"), str(item.get("status")),
                    item.get("type"), item.get("attached_id"), item.get("episode_num"), item.get("id")
                )

                if exists:
                    cursor.execute("""
                        UPDATE tvshows SET
                            lang=%s, title=%s, media_type=%s, genre=%s, distributor=%s, synopsis=%s,
                            year=%s, duration=%s, TMDbId=%s, src=%s, p_src=%s, bd_src=%s,
                            rating=%s, highlight=%s, cast=%s, direction=%s, position=%s,
                            start_date=%s, end_date=%s, ad_id=%s, is_deleted=%s, status=%s,
                            type=%s, attached_id=%s, episode_num=%s
                        WHERE id=%s
                    """, tv_data)
                else:
                    cursor.execute("""
                        INSERT INTO tvshows (
                            lang, title, media_type, genre, distributor, synopsis, year, duration,
                            TMDbId, src, p_src, bd_src, rating, highlight, cast, direction,
                            position, start_date, end_date, ad_id, is_deleted, status, type,
                            attached_id, episode_num, id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, tv_data)

                db.commit()
                output.append({"status": 200, "message": "Tvshow synced", "id": item["id"]})

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
