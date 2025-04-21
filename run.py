import requests

BASE_URL = "http://127.0.0.1:8000"

routes = [
    "/syncMovies",
    "/syncAdvertisement",
    "/sync-music-playlists",
    "/sync-music",
    "/syncAnalytics",
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