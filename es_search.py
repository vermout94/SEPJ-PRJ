import os
import torch
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModel

# Initialize Elasticsearch
index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "password")
)

# Load the model for embedding extraction
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)  # Use AutoModel, not AutoModelForCausalLM

# Function to get query embedding
def get_query_embedding(query):
    inputs = tokenizer(query, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        hidden_states = outputs.last_hidden_state  # Use hidden states
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()  # Mean pooling
    return embedding

# Generate query embedding
query = "loop"
query_embedding = get_query_embedding(query)

# Elasticsearch search query using script_score with cosine similarity
search_query = {
    "query": {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": query_embedding}
            }
        }
    }
}

# Execute search query
try:
    response = es.search(index=index_name, body=search_query)
    hits = response['hits']['hits']
    print(hits)
except Exception as e:
    print(f"Error: {e}")
