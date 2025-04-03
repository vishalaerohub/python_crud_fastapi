from fastapi import APIRouter, HTTPException
from app.models import User
from app.db import get_db_connection
# from pydantic import BaseModel
import mysql.connector

router = APIRouter()
# Get all users
@router.get("/users")
def get_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    db.close()
    return {"users": users}

# Get user by ID
@router.get("/users/{user_id}")
def get_user(user_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.close()
    return {"user": user}

# Create a new user
@router.post("/users")
def create_user(user: User):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
                   (user.name, user.email, user.age))

        db.commit()
        user_id = cursor.lastrowid
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    db.close()
    return {"message": "User created successfully", "user_id": user_id}

# Update a user
@router.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("UPDATE users SET name=%s, email=%s, age=%s WHERE id=%s",
                   (user.name, user.email, user.age, user_id))
    db.commit()
    
    db.close()
    return {"message": "User updated successfully"}

# Delete a user
@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    
    db.close()
    return {"message": "User deleted successfully"}