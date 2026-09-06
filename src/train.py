import gc
import pandas as pd
import joblib
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

ratings = pd.read_csv(
    "../data/ratings.csv",
    usecols=["userId", "movieId", "rating"],
    dtype={"userId": "int32", "movieId": "int32", "rating": "float32"}
)
movies = pd.read_csv("../data/movies.csv", dtype={"movieId": "int32"})

min_user_ratings = 20
min_movie_ratings = 20
user_counts = ratings['userId'].value_counts()
movie_counts = ratings['movieId'].value_counts()
active_users = set(user_counts[user_counts >= min_user_ratings].index)
popular_movies = set(movie_counts[movie_counts >= min_movie_ratings].index)
del user_counts, movie_counts
gc.collect()

ratings['user_ok'] = ratings['userId'].map(lambda x: x in active_users)
filtered = ratings[ratings['user_ok']].drop(columns='user_ok')
filtered = filtered[filtered['movieId'].isin(popular_movies)]
del ratings, active_users, popular_movies
gc.collect()

SAMPLE_SIZE = 1_000_000
if len(filtered) > SAMPLE_SIZE:
    filtered = filtered.sample(n=SAMPLE_SIZE, random_state=42)
    gc.collect()

reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(filtered[['userId', 'movieId', 'rating']], reader)
trainset = data.build_full_trainset()  

model = SVD(n_factors=100, random_state=42)
model.fit(trainset)

joblib.dump(model, "../models/svd_model.pkl")
filtered.to_pickle("../models/filtered_ratings.pkl")  
movies.to_pickle("../models/movies.pkl")

print("Model and supporting data saved to /models")