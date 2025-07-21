# utils/semantic_matcher.py

import openai
import os
import numpy as np
import logging

openai.api_key = os.getenv("OPENAI_API_KEY")

# Main prompt bank with representative phrases for each question
PROMPT_BANK = {
    "q1": [
        "Accounts with CM% < 30 in last quarter",
        "Clients with less than 30% margin last quarter",
        "Which accounts had margins below 30 percent",
        "Show me accounts with less than 40% margin",
        "List clients with margin below threshold"
    ],
    "q2": [
        "What caused the margin drop in Transportation segment",
        "Which cost component triggered the margin drop in a segment",
        "Why did margin fall in Transportation or any other segment",
        "Cost drivers of margin decline in a segment",
        "Breakdown of margin fall in transportation",
        "Explain margin dip in any business segment"
    ],
    "q3": ["C&B cost variation from last quarter to this"],
    "q4": ["MoM trend of C&B cost % w.r.t. revenue"],
    "q5": ["YoY, QoQ, MoM revenue trend for an account"],
    "q6": ["Accounts where realized rate dropped more than $3 or $5"],
    "q7": ["MoM Headcount change for an account"],
    "q8": ["Revenue per person trend by account"],
    "q9": ["UT% trend for last 2 quarters"],
    "q10": ["DU-wise fresher UT trends"]
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
        return [0.0] * 1536

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

    best_score = -1
    best_qid = "q1"

    for qid, prompts in prompt_bank.items():
        if isinstance(prompts, str):  # backward compatibility
            prompts = [prompts]

        for prompt in prompts:
            prompt_embedding = get_embedding(prompt)
            similarity = cosine_similarity(user_embedding, prompt_embedding)

            if similarity > best_score:
                best_score = similarity
                best_qid = qid

    return best_qid
