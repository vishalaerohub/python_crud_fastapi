from fastapi import APIRouter, HTTPException
from app.db import get_db_connection
import mysql.connector
import requests
import os

router = APIRouter()

apiEndPointBaseUrl = "https://skyviewanalytics-api.aerohub.aero/api/deviceContent/"

@router.get("/syncMovies")
def syncMovies():
    API_URL = str(apiEndPointBaseUrl) + "syncMovies"
    HEADERS = {"partner_id": "your_partner_id"}

    response = requests.get(API_URL, headers=HEADERS)
    response_data = response.json()

    return response_data
    # db = get_db_connection()
    # cursor = db.cursor(dictionary=True)
    # cursor.execute("SELECT * FROM movies")
    # movies = cursor.fetchall()

    # db.close()
    # return {"movies": movies}