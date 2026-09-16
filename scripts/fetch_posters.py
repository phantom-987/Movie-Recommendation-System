"""
One-time script: resolve a poster URL for every movie in the catalog via OMDb,
using links.csv to map MovieLens IDs to IMDb IDs. Writes models/posters.json.

Run again anytime — it skips movies it already has and only fetches new ones.
"""
import json
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["OMDB_KEY"]
ROOT = Path(__file__).parent.parent
OUT = ROOT / "models" / "posters.json"

MIN_RATINGS = 25  # must match MIN_RATINGS_FOR_BROWSE in app/catalog.py

movies = pd.read_pickle(ROOT / "models" / "movies.pkl")
ratings = pd.read_pickle(ROOT / "models" / "filtered_ratings.pkl")
links = pd.read_csv(ROOT / "data" / "links.csv")

# Only fetch posters for movies the UI can actually show.
counts = ratings.groupby("movieId").size()
wanted = set(counts[counts >= MIN_RATINGS].index)

pairs = links[links["movieId"].isin(wanted)].dropna(subset=["imdbId"])
# imdbId in links.csv is stored as a bare number (e.g. 114709) -> needs "tt" + 7 digits
pairs = [(int(r.movieId), f"tt{int(r.imdbId):07d}") for r in pairs.itertuples()]

cache = json.loads(OUT.read_text()) if OUT.exists() else {}
todo = [(m, imdb) for m, imdb in pairs if str(m) not in cache]
print(f"{len(pairs)} movies in scope, {len(todo)} still to fetch")

session = requests.Session()

def fetch(pair):
    movie_id, imdb_id = pair
    try:
        r = session.get(
            "http://www.omdbapi.com/",
            params={"i": imdb_id, "apikey": KEY},
            timeout=10,
        )
        if r.status_code != 200:
            return movie_id, None
        data = r.json()
        if data.get("Response") == "False":
            # Surface real API errors (bad key, rate limit) instead of silently
            # treating them as "no poster" — first few, then stay quiet.
            print(f"  OMDb error for {imdb_id}: {data.get('Error')}")
            return movie_id, None
        poster = data.get("Poster")
        if not poster or poster == "N/A":
            return movie_id, None
        return movie_id, poster
    except requests.RequestException:
        return movie_id, None

with ThreadPoolExecutor(max_workers=4) as pool:  # OMDb free tier is rate-limited; keep this gentle
    for i, (movie_id, poster_url) in enumerate(pool.map(fetch, todo), 1):
        cache[str(movie_id)] = poster_url  # None means "no poster, use the duotone"
        if i % 100 == 0:
            OUT.write_text(json.dumps(cache))
            print(f"  {i}/{len(todo)}")
        if i % 900 == 0:  # free tier caps at 1000/day — pause well before hitting it
            print("  approaching daily limit, sleeping 60s")
            time.sleep(60)

OUT.write_text(json.dumps(cache))
found = sum(1 for v in cache.values() if v)
print(f"done — {found}/{len(cache)} have posters")