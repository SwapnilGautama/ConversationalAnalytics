# utils/semantic_matcher.py

import openai
import os
import numpy as np
import logging

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt bank for 10 questions
PROMPT_BANK = {
    "q1": "Accounts with CM% < 30 in last quarter",
    "q2": "Which cost triggered the margin drop in transportation",
    "q3": "C&B cost variation from last quarter to this",
    "q4": "MoM trend of C&B cost % w.r.t. revenue",
    "q5": "YoY, QoQ, MoM revenue trend for an account",
    "q6": "Accounts where realized rate dropped more than $3 or $5",
    "q7": "MoM Headcount change for an account",
    "q8": "Revenue per person trend by account",
    "q9": "UT% trend for last 2 quarters",
    "q10": "DU-wise fresher UT trends"
}

# Embedding cache (optional – speeds up matching)
EMBEDDING_CACHE = {}

def get_embedding(text):
    if text in EMBEDDING_CACHE:
        return EMBEDDING_CACHE[text]

    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embedding = response["data"][0]["embedding"]
        EMBEDDING_CACHE[text] = embedding
        return embedding
    except Exception as e:
        logging.error(f"Embedding failed for '{text}': {e}")
        return None

def cosine_similarity(a, b):
    if a is None or b is None:
        return -1  # Lowest possible similarity

    a = np.array(a)
    b = np.array(b)

    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return -1

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_best_matching_question(user_query):
    user_embedding = get_embedding(user_query)
    if user_embedding is None:
        return None  # or return "q1" as fallback

    scores = {}
    for key, prompt in PROMPT_BANK.items():
        prompt_embedding = get_embedding(prompt)
        similarity = cosine_similarity(user_embedding, prompt_embedding)
        scores[key] = similarity

    best_match = max(scores, key=scores.get)
    return best_match
