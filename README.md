# Movie Recommendation System

A movie recommendation system built using collaborative filtering, trained on the 
MovieLens dataset (32 million ratings). Given a user, the system predicts and 
recommends movies they are likely to enjoy but haven't watched yet.
Most recommendation systems (like the ones used by Netflix or Amazon) work by 
learning patterns from what users have rated or purchased in the past. This project 
does the same thing on a smaller scale — it looks at how thousands of users rated 
movies, learns hidden patterns in their taste, and uses those patterns to predict 
what a specific user would rate a movie they haven't seen.


### Data Set 
**MovieLens 32M** — a public dataset from GroupLens Research containing:
- 32 million ratings
- ~200,000 users
- ~84,000 movies

NOTE- Since the full dataset is large, I filtered it to users and movies with at least 20 
ratings each, then sampled it down to 1 million ratings to keep training fast and 
manageable on a regular laptop.

## Results

I compared my model against a simple baseline (just recommending the most popular 
movies to everyone, regardless of who they are):

| Approach | Precision@10 | Recall@10 |
|---|---|---|
| Baseline (popular movies for everyone) | 0.005 | 0.046 |
| **My model (SVD)** | **0.596** | **0.585** 

recommendation-system/
├── app/ # FastAPI app (serves recommendations)
├── notebooks/ # EDA, model training, evaluation
├── src/ # training script
├── models/ # saved trained model (not in repo — see .gitignore)
├── Dockerfile
└── requirements.txt
