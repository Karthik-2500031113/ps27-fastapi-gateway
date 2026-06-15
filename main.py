from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import requests
import numpy as np

from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# ---------------- CORS ---------------- #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- URLS ---------------- #

SPRING_URL = "http://localhost:8081"
NODE_URL = "http://localhost:5000"

# ---------------- MONGODB ---------------- #

client = MongoClient(
    "mongodb://localhost:27017"
)

db = client["service_request_logs"]

embeddings_collection = db["service_embeddings"]

interaction_collection = db["interaction_history"]

# ---------------- AI MODEL ---------------- #

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# ---------------- HOME ---------------- #

@app.get("/")
def home():

    return {
        "message": "FastAPI Running"
    }

# ---------------- USERS ---------------- #

@app.get("/users")
def get_users():

    response = requests.get(
        f"{SPRING_URL}/users"
    )

    return response.json()

# ---------------- REQUESTS ---------------- #

@app.get("/requests")
def get_requests(
        role: str,
        email: str):

    response = requests.get(

        f"{SPRING_URL}/requests",

        params={
            "role": role,
            "email": email
        }
    )

    return response.json()

@app.post("/requests")
def create_request(data: dict):

    response = requests.post(
        f"{SPRING_URL}/requests",
        json=data
    )

    return response.json()

# ---------------- RESOLVE ---------------- #

@app.put("/requests/{id}/resolve")
def resolve_request(id: int):

    response = requests.put(
        f"{SPRING_URL}/requests/{id}/resolve"
    )

    return response.json()

# ---------------- DELETE ---------------- #

@app.delete("/requests/{id}")
def delete_request(id: int):

    response = requests.delete(
        f"{SPRING_URL}/requests/{id}"
    )

    return {
        "message": "Deleted Successfully"
    }

# ---------------- ANALYTICS ---------------- #

@app.get("/analytics")
def get_analytics():

    response = requests.get(
        f"{SPRING_URL}/analytics"
    )

    return response.json()

# ---------------- NODE SEARCH ---------------- #

@app.post("/semantic-search")
def node_search(data: dict):

    response = requests.post(
        f"{NODE_URL}/api/search",
        json=data
    )

    return response.json()

# ---------------- LOGS ---------------- #

@app.get("/logs")
def get_logs():

    response = requests.get(
        f"{NODE_URL}/api/logs"
    )

    return response.json()

# ---------------- GENERATE EMBEDDING ---------------- #

@app.post("/generate_embedding")
def generate_embedding(data: dict):

    text = data["text"]

    embedding = model.encode(
        text
    ).tolist()

    embeddings_collection.insert_one({

        "requestId":
        data["requestId"],

        "text":
        text,

        "embedding":
        embedding
    })

    return {

        "message":
        "Embedding Stored"
    }

# ---------------- SEMANTIC SEARCH ---------------- #

@app.post("/semantic_search")
def semantic_search(data: dict):

    query = data["query"]

    interaction_collection.insert_one({

        "query":
        query
    })

    query_embedding = model.encode(
        query
    ).reshape(1, -1)

    documents = list(
        embeddings_collection.find()
    )

    results = []

    for doc in documents:

        similarity = cosine_similarity(

            query_embedding,

            np.array(
                doc["embedding"]
            ).reshape(1, -1)

        )[0][0]

        results.append({

            "requestId":
            doc["requestId"],

            "text":
            doc["text"],

            "score":
            float(similarity)
        })

    results.sort(

        key=lambda x: x["score"],

        reverse=True
    )

    return results[:5]

# ---------------- AI CATEGORY ---------------- #

@app.post("/categorize")
def categorize(data: dict):

    text = data["text"].lower()

    if (
        "wifi" in text
        or "network" in text
        or "internet" in text
    ):
        return {
            "category":
            "Network"
        }

    if (
        "printer" in text
        or "hardware" in text
    ):
        return {
            "category":
            "Hardware"
        }

    if (
        "software" in text
        or "login" in text
    ):
        return {
            "category":
            "Software"
        }

    return {
        "category":
        "General"
    }
@app.get("/user-analytics")
def user_analytics(email: str):

    response = requests.get(
        f"{SPRING_URL}/analytics/user",
        params={
            "email": email
        }
    )

    return response.json()