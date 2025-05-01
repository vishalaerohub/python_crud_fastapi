from app.utils.usbpath import find_usb_mount_path
import csv
usb_path = find_usb_mount_path()

def read_db(db_name):
    sql_path = f"{usb_path}/content/database/{db_name}.csv"
    with open(sql_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        output = []
        for row in reader:
            output.append(row)

    return output