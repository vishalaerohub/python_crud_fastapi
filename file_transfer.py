import mysql.connector
import shutil
import os
from datetime import datetime

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="your_user",
        password="your_password",
        database="file_manager"
    )

# Function to move files based on date conditions
def process_files():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Get current date
    current_date = datetime.now().date()

    # Fetch pending files (media_status = 0)
    cursor.execute("SELECT * FROM media_files WHERE media_status = 0")
    files = cursor.fetchall()

    if not files:
        print("No files pending for transfer.")
        return

    for file in files:
        file_id = file["id"]
        source_path = file["source_path"]
        destination_path = file["destination_path"]
        start_date = file["start_date"]

        # If start_date > current_date, keep status = 0
        if start_date > current_date:
            print(f"Skipping file {file['file_name']}: Transfer scheduled for {start_date}")
            continue

        # Move file if the date is valid
        try:
            if os.path.exists(source_path):
                shutil.move(source_path, destination_path)
                print(f"File {file['file_name']} moved successfully.")
                
                # Update status in database (mark as transferred)
                cursor.execute("UPDATE media_files SET media_status = 1 WHERE id = %s", (file_id,))
                db.commit()
            else:
                print(f"Error: Source file {source_path} not found.")

        except Exception as e:
            print(f"Error moving file {file['file_name']}: {e}")

    db.close()

# Run the script
if __name__ == "__main__":
    process_files()
