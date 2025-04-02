from fastapi import APIRouter, HTTPException
from db import get_db_connection
from pydantic import BaseModel
import mysql.connector

router = APIRouter()

class Post(BaseModel):
    title: str
    content: str
    author_id: int

@router.get("/posts")
def get_posts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()

    db.close()
    return {"posts": posts}


@router.post("/posts")
def create_posts(post: Post):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:

        cursor.execute("INSERT INTO posts (title, content, author_id) VALUE (%s, %s, %s)", (post.title, post.content, post.author_id))
        db.commit()
        post_id = cursor.lastrowid
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="title already available in records")

    db.close()
    return {"message": "User created successfully", "post_id": post_id}
