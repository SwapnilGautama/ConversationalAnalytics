import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Updated PROMPT BANK with dynamic Q2 intent
PROMPT_BANK = {
    "Q1": [
        "Which accounts had CM% < 30 in the last quarter?",
        "Clients with less than 30% margin last quarter",
        "Which accounts had margins below 30 percent",
        "Show me accounts with less than 40% margin",
        "List clients with margin below threshold"
    ],
    "Q2": [
        "Which cost caused margin drop last month?",
        "Which cost increased last month vs previous month?",
        "What caused margin drop in Transportation?",
        "Which cost item triggered margin decline last month?",
        "Why did margin fall last month in Manufacturing?",
        "Last month's margin dropped — what cost increased?",
        "Find clients with higher costs and lower margin this month",
        "Margin dropped in Automotive — which cost increased?",
        "Identify cost buckets responsible for margin drop",
        "Segment-wise cost increase that led to margin decline"
    ],
    "Q3": [
        "Compare C&B cost by segment over two quarters",
        "Which segments had highest C&B change",
        "Show C&B cost trend by segment",
        "C&B cost comparison Q1 vs Q2 by segment",
        "Segment wise change in C&B cost"
    ],
        "Q4": [
        "What is the MoM trend of C&B cost?",
        "C&B vs revenue monthly trend",
        "Month over month comparison of C&B with revenue",
        "C&B cost as percentage of revenue trend",
        "Compare C&B cost % with revenue monthly"
    ]

}

# Flatten prompt bank into parallel lists
questions, qids = [], []
for qid, qlist in PROMPT_BANK.items():
    for q in qlist:
        questions.append(q)
        qids.append(qid)

# Precompute question embeddings
question_embeddings = model.encode(questions)

def find_best_matching_qid(user_query):
    query_embedding = model.encode([user_query])[0]
    similarities = util.cos_sim(query_embedding, question_embeddings)[0]
    best_idx = similarities.argmax().item()
    best_qid = qids[best_idx]
    matched_question = questions[best_idx]
    return best_qid, matched_question
