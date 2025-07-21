import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define your prompt bank
PROMPT_BANK = {
    "Q1": [
        "Which accounts had CM% < 30 in the last quarter?",
        "Clients with less than 30% margin last quarter",
        "Which accounts had margins below 30 percent",
        "Show me accounts with less than 40% margin",
        "List clients with margin below threshold"
    ],
    "Q2": [
        "What caused the margin drop in Transportation?",
        "Explain margin decline in Transportation segment",
        "Why did margin fall for Transportation last quarter?",
        "Root cause for low margin in Transportation",
        "Transportation margin drop reason"
    ]
}

# Create a flat list of (question, qid)
questions = []
qids = []
for qid, qlist in prompt_bank.items():
    for q in qlist:
        questions.append(q)
        qids.append(qid)

# Precompute embeddings for all questions
question_embeddings = model.encode(questions)

def find_best_matching_qid(user_query):
    # Compute embedding for user query
    query_embedding = model.encode([user_query])[0]

    # Compute similarity scores
    similarities = util.cos_sim(query_embedding, question_embeddings)[0]

    # Find the index of the highest similarity
    best_idx = similarities.argmax().item()
    best_qid = qids[best_idx]

    # Optionally return matched text as well
    matched_question = questions[best_idx]
    return best_qid, matched_question
