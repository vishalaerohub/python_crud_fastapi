from fastapi import FastAPI, HTTPException
from app.db import get_db_connection
from app.routes.users import router as users_router
from app.routes.sync import router as sync_router

app = FastAPI()

app.include_router(users_router)
app.include_router(sync_router)
