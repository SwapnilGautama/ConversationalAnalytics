# utils/semantic_matcher.py

import openai
import os
import numpy as np

# Load your prompt bank (can be extended)
PROMPT_BANK = {
    "q1": "Accounts with CM% < 30 in last quarter",
    "q2": "Which cost triggered the margin drop in transportation",
    "q3": "C&B cost variation from last quarter to this",
    "q4": "MoM trend of C&B cost % w.r.t. revenue",
    "q5": "YoY QoQ MoM revenue for account",
    "q6": "Realized rate drop more than $3/$5",
    "q7": "MoM Headcount change for an account",
    "q8": "Revenue per person trend by account",
    "q9": "UT% trend for last 2 quarters",
    "q10": "DU wise fresher UT trends"
}

def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_best_matching_question(user_query):
    user_embedding = get_embedding(user_query)
    scores = {}

    for key, prompt in PROMPT_BANK.items():
        prompt_embedding = get_embedding(prompt)
        similarity = cosine_similarity(user_embedding, prompt_embedding)
        scores[key] = similarity

    best_match = max(scores, key=scores.get)
    return best_match
