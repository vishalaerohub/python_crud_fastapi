import mysql.connector
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pass@123",
        database="master_sirium"
    )