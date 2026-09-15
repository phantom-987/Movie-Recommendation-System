import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import catalog
from app.recommender import get_recommendations

app = FastAPI(
    title="Movie Recommendation API",
    description="SVD collaborative filtering over MovieLens, served to a React front end.",
    version="2.0.0",
)

# Vite dev server runs on 5173. Override with ALLOWED_ORIGINS="https://your.app"
_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "movies_in_catalog": int(len(catalog.CATALOG)),
        "genres": len(catalog.ALL_GENRES),
    }


@app.get("/genres")
def genres():
    """Every genre, with a movie count. Feeds the genre picker."""
    return {"genres": catalog.list_genres()}


@app.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(12, ge=1, le=50)):
    """Title search. Feeds the search box that drives 'more like this'."""
    return {"query": q, "results": catalog.search_movies(q, limit)}


@app.get("/movies/{movie_id}")
def movie_detail(movie_id: int):
    try:
        return catalog.get_movie(movie_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0])


@app.get("/movies/{movie_id}/similar")
def movie_similar(movie_id: int, n: int = Query(5, ge=1, le=20)):
    """Feature 2: five movies like this one."""
    try:
        seed = catalog.get_movie(movie_id)
        return {"seed": seed, "similar": catalog.similar_movies(movie_id, n)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0])


@app.get("/recommend/genre")
def recommend_genre(
    genres: str = Query(..., description="One or more genres, comma separated"),
    n: int = Query(18, ge=1, le=60),
    user_id: int | None = None,
):
    """
    Feature 1: recommendations for the genres someone picked.

    Pass user_id to personalise the ranking with the trained model; leave it
    off and the ranking is popularity-weighted instead.
    """
    wanted = [g.strip() for g in genres.split(",") if g.strip()]
    payload = catalog.recommend_by_genre(wanted, n=n, user_id=user_id)
    if not payload["genres"]:
        raise HTTPException(
            status_code=400,
            detail=f"No known genres in {wanted!r}. Call /genres for the valid list.",
        )
    return payload


@app.get("/sections")
def sections(n: int = Query(18, ge=1, le=40), user_id: int | None = None):
    """Feature 3: the genre rows for the home screen."""
    return {
        "user_id": user_id,
        "sections": catalog.home_sections(n=n, user_id=user_id),
    }


@app.get("/recommend/{user_id}")
def recommend(user_id: int, n: int = Query(10, ge=1, le=50)):
    """Original endpoint: top predictions for a user across every genre."""
    try:
        return {"user_id": user_id, "recommendations": get_recommendations(user_id, n)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))