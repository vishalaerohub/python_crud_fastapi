
from fastapi import FastAPI, HTTPException
from app.db import get_db_connection
# from app.routes.users import router as users_router
from app.routes.sync import router as sync_router
from app.routes.sync_movies import router as sync_movie_router
from app.routes.synctvshows import router as synctvshows_router 
from app.routes.sync_magazine import router as syncMagazine_router
from app.routes.sync_games import router as syncgames_router
from app.routes.sync_shopping import router as syncshopping_router
from app.routes.sync_cityscape import router as sync_cityscape_router
from app.routes.sync_music import router as sync_music_router
from app.routes.database import router as sync_db_router
from app.routes.sync_music_playlists import router as sync_music_playlists_router

app = FastAPI()

app.include_router(sync_db_router)
app.include_router(sync_movie_router)
app.include_router(synctvshows_router)
app.include_router(sync_router)
app.include_router(syncMagazine_router)
app.include_router(syncgames_router)
app.include_router(sync_cityscape_router)
app.include_router(syncshopping_router)
app.include_router(syncshopping_router)
app.include_router(sync_cityscape_router)
app.include_router(sync_music_router)
app.include_router(sync_music_playlists_router)