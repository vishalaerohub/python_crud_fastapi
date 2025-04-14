from fastapi import FastAPI, HTTPException
from app.db import get_db_connection
# from app.routes.users import router as users_router
from app.routes.sync import router as sync_router
from app.routes.synctvshows import router as synctvshows_router 
from app.routes.sync_magazine import router as syncMagazine_router
from app.routes.sync_games import router as syncgames_router


app = FastAPI()

# app.include_router(users_router)
app.include_router(sync_router)
app.include_router(synctvshows_router)
app.include_router(syncMagazine_router)
app.include_router(syncgames_router)