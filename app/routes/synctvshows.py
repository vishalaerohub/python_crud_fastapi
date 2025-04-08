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
    API_URL = str(apiEndPointBaseUrl) + "syncTvshows"
    HEADERS = {"partner-id": "AEROADVE20240316A377"}

    try:
        response = requests.get(API_URL, headers=HEADERS)
        response_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching API: {e}")

    print("✅ API Fetched:", len(response_data.get("data", [])))
    return {"status": True, "sample": response_data["data"][0] if response_data.get("data") else {}}


    if not response_data.get("data"):
        return {
            "data": "Data is not available",
            "status": False,
            "code": 404
        }

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    output = []

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

            tv_data = (
                item["lang"], item["title"], item["media_type"], item["genre"], item["distributor"],
                item["synopsis"], item["year"], item["country"], item["duration"], item["TMDbId"],
                item["src"], item["p_src"], item["bd_src"], item["rating"], item["Highlight_home"],
                item["Highlight"], item["cast"], item["direction"], item["eds_object"], item["position"],
                item["start_date"], item["end_date"], ad_id, item["is_deleted"], str(item["status"]),
                item["type"], item["attached_id"], item["episode_num"], item["id"] 
            )

            if exists:
                cursor.execute("""
                    UPDATE tvshows SET
                        lang=%s, title=%s, media_type=%s, genre=%s, distributor=%s, synopsis=%s,
                        year=%s, country=%s, duration=%s, TMDbId=%s, src=%s, p_src=%s, bd_src=%s,
                        rating=%s, highlight_home=%s, highlight=%s, cast=%s, direction=%s, eds_object=%s,
                        position=%s, start_date=%s, end_date=%s, ad_id=%s, is_deleted=%s, status=%s,
                        type=%s, attached_id=%s, episode_num=%s
                    WHERE id=%s
                """, tv_data)
            else:
                cursor.execute("""
                    INSERT INTO tvshows (
                        lang, title, media_type, genre, distributor, synopsis, year, country, duration,
                        TMDbId, src, p_src, bd_src, rating, highlight_home, highlight, cast, direction,
                        eds_object, position, start_date, end_date, ad_id, is_deleted, status, type,
                        attached_id, episode_num, id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, tv_data)

            db.commit()

            output.append({
                "status": 200,
                "message": "Tvshow synced successfully",
                "id": item["id"]
            })

    db.close()

    return {
        "status": True,
        "message": "Sync complete",
        "results": output
    }
