from fastapi import APIRouter
import csv
# import subprocess

from app.utils.usbpath import find_usb_mount_path

usb_path = find_usb_mount_path()

router = APIRouter()

@router.get('/read-db')
def read_db():
    sql_path = f"{usb_path}/content/database/movies.csv"
    with open(sql_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        output = []
        for row in reader:
            output.append(row)

    return {"data": output}