# utils/semantic_matcher.py

import os
import json
import hashlib
import numpy as np
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Cache folder for prompt embeddings
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
    """Generate cache file path based on hashed input text"""
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{text_hash}.json")

def get_cached_prompt_embedding(text):
    """Retrieve embedding from cache or generate and store it"""
    cache_path = get_embedding_cache_path(text)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If corrupted, delete and regenerate
            os.remove(cache_path)

    embedding = get_embedding(text)
    # Convert to list explicitly to ensure JSON serializability
    embedding_list = list(embedding)
    with open(cache_path, "w") as f:
        json.dump(embedding_list, f)
    return embedding_list

def get_user_embedding(user_query):
    """Get embedding for user's query (no caching for live queries)"""
    return get_embedding(user_query)

def get_best_matching_question(user_query: str, prompt_bank: dict):
    """Return the best matching prompt ID from the prompt bank"""
    user_embedding = get_user_embedding(user_query)
    scores = {}

    for key, prompt in prompt_bank.items():
        prompt_embedding = get_cached_prompt_embedding(prompt)
        similarity = cosine_similarity(user_embedding, prompt_embedding)
        scores[key] = similarity

    best_match = max(scores, key=scores.get)
    return best_match
