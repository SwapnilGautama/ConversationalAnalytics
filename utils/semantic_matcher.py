# utils/semantic_matcher.py

import os
import json
import hashlib
import numpy as np
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Optional: Cache folder to avoid repeated embedding calls
CACHE_DIR = "utils/.embedding_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_embedding(text):
    """Fetch embedding using OpenAI API"""
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding_cache_path(text):
    """Generate file path for caching based on text hash"""
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{text_hash}.json")

def get_cached_prompt_embedding(text):
    """Retrieve embedding from cache or generate and store if not found"""
    cache_path = get_embedding_cache_path(text)
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    else:
        embedding = get_embedding(text)
        with open(cache_path, "w") as f:
            json.dump(embedding, f)
        return embedding

def get_user_embedding(user_query):
    """Fetch embedding for user input without caching"""
    return get_embedding(user_query)

def get_best_matching_question(user_query: str, prompt_bank: dict):
    """
    Compute the best matching prompt ID using cosine similarity.

    Args:
        user_query (str): User's question.
        prompt_bank (dict): Dictionary of prompt_id -> question string.

    Returns:
        str: Best matching question ID (e.g., 'q3')
    """
    user_embedding = get_user_embedding(user_query)
    scores = {}

    for key, prompt in prompt_bank.items():
        prompt_embedding = get_cached_prompt_embedding(prompt)
        similarity = cosine_similarity(user_embedding, prompt_embedding)
        scores[key] = similarity

    best_match = max(scores, key=scores.get)
    return best_match
