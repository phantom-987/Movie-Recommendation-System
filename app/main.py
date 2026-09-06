from fastapi import FastAPI, HTTPException
from app.recommender import get_recommendations

app = FastAPI(title="Movie Recommendation API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/recommend/{user_id}")
def recommend(user_id: int, n: int = 10):
    try:
        recs = get_recommendations(user_id, n)
        return {"user_id": user_id, "recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))