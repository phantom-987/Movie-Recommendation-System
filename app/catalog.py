"""
Catalog + content layer.

recommender.py already gives us user-based collaborative filtering (SVD).
This module adds everything the UI needs on top of the same artifacts:

  - a clean movie catalog (title / year / genres / popularity stats)
  - genre listing + genre browsing
  - title search
  - item-to-item similarity, taken from the SVD model's learned item factors
    (model.qi) and re-ranked by genre overlap

No new training and no new files: it reuses models/svd_model.pkl,
models/movies.pkl and models/filtered_ratings.pkl.
"""

import re
from functools import lru_cache

import numpy as np
import pandas as pd
import json
from pathlib import Path

from app.recommender import model, movies, filtered_ratings

POSTER_BASE_FALLBACK = None  # OMDb gives full URLs already, no base needed
_POSTER_FILE = Path(__file__).parent.parent / "models" / "posters.json"

if _POSTER_FILE.exists():
    POSTERS = {int(k): v for k, v in json.loads(_POSTER_FILE.read_text()).items() if v}
else:
    POSTERS = {}

# Rows shown in the Netflix-style home screen, in order.
HOME_GENRES = [
    "Horror",
    "Action",
    "Sci-Fi",
    "Romance",
    "Comedy",
    "Thriller",
    "Animation",
    "Documentary",
]

# A movie needs at least this many ratings before it can show up in a
# browse row or a "similar movies" list. Keeps obscure noise out of the UI.
MIN_RATINGS_FOR_BROWSE = 25

_YEAR_RE = re.compile(r"\((\d{4})\)\s*$")


def _split_title(raw_title: str):
    """'Toy Story (1995)' -> ('Toy Story', 1995)"""
    raw_title = str(raw_title).strip()
    match = _YEAR_RE.search(raw_title)
    if not match:
        return raw_title, None
    return _YEAR_RE.sub("", raw_title).strip(), int(match.group(1))


def _build_catalog() -> pd.DataFrame:
    stats = (
        filtered_ratings.groupby("movieId")["rating"]
        .agg(rating_count="count", rating_mean="mean")
        .reset_index()
    )

    cat = movies.merge(stats, on="movieId", how="inner")

    titles = cat["title"].map(_split_title)
    cat["clean_title"] = [t for t, _ in titles]
    cat["year"] = [y for _, y in titles]
    cat["search_key"] = cat["clean_title"].str.lower()

    cat["genres"] = cat["genres"].fillna("")
    cat["genre_list"] = cat["genres"].str.split("|").map(
        lambda gs: [g for g in gs if g and g != "(no genres listed)"]
    )

    # Bayesian average: pulls thinly-rated movies toward the global mean so a
    # single 5.0 rating can't outrank a classic.
    global_mean = filtered_ratings["rating"].mean()
    prior = cat["rating_count"].quantile(0.75)
    cat["score"] = (
        cat["rating_count"] * cat["rating_mean"] + prior * global_mean
    ) / (cat["rating_count"] + prior)

    return cat.set_index("movieId", drop=False).sort_values("score", ascending=False)


CATALOG = _build_catalog()

ALL_GENRES = sorted({g for gs in CATALOG["genre_list"] for g in gs})


# --------------------------------------------------------------------------
# Item factors -> similarity
# --------------------------------------------------------------------------

def _build_item_space():
    """Unit-normalised SVD item factors, so cosine similarity is a dot product."""
    trainset = model.trainset
    raw_ids, inner_ids = [], []
    for inner in trainset.all_items():
        raw_ids.append(int(trainset.to_raw_iid(inner)))
        inner_ids.append(inner)

    factors = model.qi[inner_ids]
    norms = np.linalg.norm(factors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-9
    factors = factors / norms

    row_of = {raw: i for i, raw in enumerate(raw_ids)}
    return factors, np.array(raw_ids), row_of


ITEM_FACTORS, ITEM_RAW_IDS, ITEM_ROW = _build_item_space()


def _genre_overlap(a: list, b: list) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb)


# --------------------------------------------------------------------------
# Serialisation
# --------------------------------------------------------------------------

def _row_to_dict(row, **extra) -> dict:
    out = {
        "movie_id": int(row.movieId),
        "title": row.clean_title,
        "year": int(row.year) if pd.notna(row.year) else None,
        "genres": list(row.genre_list),
        "rating_count": int(row.rating_count),
        "avg_rating": round(float(row.rating_mean), 2),
        "poster_url": POSTERS.get(int(row.movieId)),
    }
    out.update(extra)
    return out


def _frame_to_list(df: pd.DataFrame) -> list:
    return [_row_to_dict(row) for row in df.itertuples()]


# --------------------------------------------------------------------------
# Public API used by main.py
# --------------------------------------------------------------------------

def list_genres() -> list:
    """Every genre in the catalog, with how many movies it holds."""
    counts = {}
    for gs in CATALOG["genre_list"]:
        for g in gs:
            counts[g] = counts.get(g, 0) + 1
    return [{"genre": g, "movie_count": counts[g]} for g in ALL_GENRES]


def get_movie(movie_id: int) -> dict:
    if movie_id not in CATALOG.index:
        raise KeyError(f"movie {movie_id} is not in the catalog")
    return _row_to_dict(CATALOG.loc[movie_id])


def search_movies(query: str, limit: int = 12) -> list:
    query = (query or "").strip().lower()
    if not query:
        return []

    hits = CATALOG[CATALOG["search_key"].str.contains(re.escape(query), na=False)]
    if hits.empty:
        return []

    # Exact and prefix matches first, then whatever is most rated.
    starts = hits["search_key"].str.startswith(query)
    hits = hits.assign(_rank=np.where(hits["search_key"] == query, 0, np.where(starts, 1, 2)))
    hits = hits.sort_values(["_rank", "rating_count"], ascending=[True, False])
    return _frame_to_list(hits.head(limit))


@lru_cache(maxsize=512)
def _genre_pool(genre: str) -> tuple:
    mask = CATALOG["genre_list"].map(lambda gs: genre in gs)
    pool = CATALOG[mask & (CATALOG["rating_count"] >= MIN_RATINGS_FOR_BROWSE)]
    return tuple(int(m) for m in pool["movieId"])


def browse_genre(genre: str, n: int = 18, offset: int = 0) -> list:
    """Best-rated movies in a genre, popularity-weighted. No user needed."""
    ids = _genre_pool(genre)
    if not ids:
        return []
    pool = CATALOG.loc[list(ids)].sort_values("score", ascending=False)
    return _frame_to_list(pool.iloc[offset : offset + n])


def similar_movies(movie_id: int, n: int = 5) -> list:
    """
    Movies that behave like this one.

    Similarity comes from the SVD item factors, i.e. 'people who liked this
    also liked that', then gets nudged by genre overlap so the list stays
    recognisable to a human. Falls back to genre matching for movies the
    model never saw.
    """
    if movie_id not in CATALOG.index:
        raise KeyError(f"movie {movie_id} is not in the catalog")

    seed = CATALOG.loc[movie_id]
    seed_genres = list(seed.genre_list)

    if movie_id not in ITEM_ROW:
        return _fallback_similar(movie_id, seed_genres, n)

    sims = ITEM_FACTORS @ ITEM_FACTORS[ITEM_ROW[movie_id]]
    sims = (sims + 1.0) / 2.0  # cosine is -1..1; map to 0..1

    frame = pd.DataFrame({"movieId": ITEM_RAW_IDS, "latent": sims})
    frame = frame[frame["movieId"] != movie_id]
    frame = frame.merge(
        CATALOG[["movieId", "genre_list", "rating_count"]].reset_index(drop=True),
        on="movieId",
        how="inner",
    )
    frame = frame[frame["rating_count"] >= MIN_RATINGS_FOR_BROWSE]
    if frame.empty:
        return _fallback_similar(movie_id, seed_genres, n)

    # Only the top slice is worth the genre pass.
    frame = frame.nlargest(min(400, len(frame)), "latent")
    frame["genre_sim"] = frame["genre_list"].map(lambda gs: _genre_overlap(seed_genres, gs))
    frame["match"] = 0.75 * frame["latent"] + 0.25 * frame["genre_sim"]
    frame = frame.nlargest(n, "match")

    return [
        _row_to_dict(CATALOG.loc[int(r.movieId)], match=round(float(r.match), 3))
        for r in frame.itertuples()
    ]


def _fallback_similar(movie_id: int, seed_genres: list, n: int) -> list:
    pool = CATALOG[CATALOG["rating_count"] >= MIN_RATINGS_FOR_BROWSE].copy()
    pool = pool[pool["movieId"] != movie_id]
    pool["genre_sim"] = pool["genre_list"].map(lambda gs: _genre_overlap(seed_genres, gs))
    pool = pool[pool["genre_sim"] > 0]
    if pool.empty:
        return []
    pool["match"] = 0.7 * pool["genre_sim"] + 0.3 * (pool["score"] / 5.0)
    pool = pool.nlargest(n, "match")
    return [
        _row_to_dict(row, match=round(float(row.match), 3)) for row in pool.itertuples()
    ]


def knows_user(user_id: int) -> bool:
    return bool((filtered_ratings["userId"] == user_id).any())


def recommend_by_genre(genres: list, n: int = 18, user_id: int | None = None) -> dict:
    """
    Pick movies for one or more genres.

    With a known user_id the SVD model predicts that user's rating for every
    unseen movie in those genres. Without one, it falls back to the
    popularity-weighted ranking so the page is never empty.
    """
    genres = [g for g in genres if g in ALL_GENRES]
    if not genres:
        return {"personalized": False, "genres": [], "results": []}

    ids = set()
    for g in genres:
        ids.update(_genre_pool(g))
    if not ids:
        return {"personalized": False, "genres": genres, "results": []}

    if user_id is None or not knows_user(user_id):
        pool = CATALOG.loc[list(ids)].sort_values("score", ascending=False)
        return {
            "personalized": False,
            "genres": genres,
            "results": _frame_to_list(pool.head(n)),
        }

    seen = set(filtered_ratings.loc[filtered_ratings["userId"] == user_id, "movieId"])
    candidates = [m for m in ids if m not in seen]

    scored = sorted(
        ((m, model.predict(user_id, m).est) for m in candidates),
        key=lambda x: x[1],
        reverse=True,
    )[:n]

    return {
        "personalized": True,
        "genres": genres,
        "results": [
            _row_to_dict(CATALOG.loc[m], predicted_rating=round(float(est), 2))
            for m, est in scored
        ],
    }


def home_sections(n: int = 18, user_id: int | None = None) -> list:
    """The genre rows for the home screen."""
    personalize = user_id is not None and knows_user(user_id)
    sections = []
    for genre in HOME_GENRES:
        if genre not in ALL_GENRES:
            continue
        if personalize:
            payload = recommend_by_genre([genre], n=n, user_id=user_id)
            items = payload["results"]
        else:
            items = browse_genre(genre, n=n)
        if items:
            sections.append(
                {"genre": genre, "personalized": personalize, "items": items}
            )
    return sections