import os
import shutil
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Function to create the MySQL database and table
def create_db():
    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='Pass@123',  # Replace with your MySQL password
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS file_manager")
            cursor.execute("USE file_manager")

            # Create table for storing file data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255),
                    source_path TEXT,
                    destination_path TEXT,
                    date_moved TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            print("Database and table created successfully.")
            cursor.close()

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

# Function to insert file data into the MySQL database
def update_database(file_name, source_path, destination_path):
    try:
        # Establish connection to the MySQL database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='password',  # Replace with your MySQL password
            database='file_manager'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO files (file_name, source_path, destination_path)
                VALUES (%s, %s, %s)
            ''', (file_name, source_path, destination_path))

            # Commit changes and close the cursor
            connection.commit()
            cursor.close()
            print(f"File data for {file_name} inserted into database.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

# Function to move the file and update the database
def move_file(source_path, destination_path):
    # Create the destination directory if it doesn't exist
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Move the file
    shutil.move(source_path, destination_path)

    # Get the file name
    file_name = os.path.basename(source_path)

    # Update the database with the file details
    update_database(file_name, source_path, destination_path)

# Function to handle files in the source folder and move them
def handle_files(source_folder, destination_folder):
    # Iterate through files in the source folder
    for file_name in os.listdir(source_folder):
        source_path = os.path.join(source_folder, file_name)

        if os.path.isfile(source_path):
            destination_path = os.path.join(destination_folder, file_name)

            try:
                # Move the file and update the database
                move_file(source_path, destination_path)
                print(f"Moved {file_name} to {destination_path}")
            except Exception as e:
                print(f"Error moving {file_name}: {e}")

if __name__ == "__main__":
    # Create the database and table
    create_db()

    # Source folder (e.g., USB or another directory)
    source_folder = "/path/to/source/folder"
    
    # Destination folder (e.g., Sirium Box storage or another directory)
    destination_folder = "/path/to/destination/folder"
    
    # Call the handle_files function to move files and update the database
    handle_files(source_folder, destination_folder)
