import joblib
import pandas as pd
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"

model = joblib.load(MODEL_DIR / "svd_model.pkl")
filtered_ratings = pd.read_pickle(MODEL_DIR / "filtered_ratings.pkl")
movies = pd.read_pickle(MODEL_DIR / "movies.pkl")

def get_recommendations(user_id: int, n: int = 10) -> list:
    rated_movies = filtered_ratings[filtered_ratings['userId'] == user_id]['movieId'].unique()

    if len(rated_movies) == 0:
        # Cold-start: user not in training data — fall back to popularity
        popular = filtered_ratings.groupby('movieId').size().sort_values(ascending=False).head(n)
        result = movies[movies['movieId'].isin(popular.index)][['movieId', 'title']]
        result['predicted_rating'] = None
        result['note'] = 'cold_start_fallback'
        return result.to_dict(orient='records')

    all_movies = movies['movieId'].unique()
    unrated_movies = [m for m in all_movies if m not in rated_movies]

    predictions = [
        (movie_id, model.predict(user_id, movie_id).est)
        for movie_id in unrated_movies
    ]
    top_n = sorted(predictions, key=lambda x: x[1], reverse=True)[:n]

    result = pd.DataFrame(top_n, columns=['movieId', 'predicted_rating'])
    result = result.merge(movies[['movieId', 'title']], on='movieId')
    return result[['movieId', 'title', 'predicted_rating']].to_dict(orient='records')