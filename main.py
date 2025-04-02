from fastapi import FastAPI, HTTPException
from db import get_db_connection
from test import router as posts_router
from users import router as users_router

app = FastAPI()

app.include_router(users_router)
app.include_router(posts_router)
