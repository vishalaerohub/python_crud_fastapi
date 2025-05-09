import os
import subprocess
import time
import requests

project_path = "/home/vishal/aerohub/python_crud_fastapi"
venv_activate = os.path.join(project_path, "venv/bin/activate")
main_app = "app.main:app"

# 1. Start uvicorn in background
uvicorn_cmd = f"cd {project_path} && source {venv_activate} && uvicorn {main_app} --reload"
process = subprocess.Popen(['/bin/bash', '-c', uvicorn_cmd])

# 2. Wait for server to boot
print("Starting FastAPI server...")
time.sleep(5)

# 3. Send sync requests
BASE_URL = "http://127.0.0.1:8000"
routes = [
    "/syncMovies",
    "/syncAdvertisement",
    "/sync-music-playlists",
    "/sync-music",
    # "/syncAnalytics",
    "/syncTvshows",
    "/syncMagazine",
    "/sync-games",
    "/syncCityscape",
    "/sync-shopping",
]

for route in routes:
    try:
        response = requests.get(BASE_URL + route)
        print(f"{route}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to call {route}: {e}")

# (Optional) Stop the server after syncing
process.terminate()
        
