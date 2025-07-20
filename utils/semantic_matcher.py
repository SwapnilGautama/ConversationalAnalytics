# utils/semantic_matcher.py

import openai
import os
import numpy as np
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")

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
        return [0.0] * 1536  # Fallback zero vector

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    if len(a) != len(b) or np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return -1

    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_best_matching_question(user_query, prompt_bank):
    user_embedding = get_embedding(user_query)
    if user_embedding is None or sum(user_embedding) == 0.0:
        logging.error("Failed to get user embedding.")
        return "q1"  # Safe fallback

    scores = {}
    for key, prompt in PROMPT_BANK.items():
        prompt_embedding = get_embedding(prompt)
        similarity = cosine_similarity(user_embedding, prompt_embedding)
        scores[key] = similarity

    best_match = max(scores, key=scores.get)
    return best_match
