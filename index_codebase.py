import os
import hashlib
import json
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Elasticsearch Configuration
index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# File to store hashes
hash_file = "file_hashes.json"

# Retrieve Elasticsearch credentials
es_user = os.getenv("ES_USERNAME", "elastic")
es_password = os.getenv("ES_PASSWORD", "changeme")
es_host = os.getenv("ES_HOST", "http://localhost:9200")

# Initialize Elasticsearch client
es = Elasticsearch(
    hosts=[es_host],
    basic_auth=(es_user, es_password),
    verify_certs=False,
)

# Load Hugging Face model
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)

# Path to the codebase directory
codebase_directory = "./test_files/"

# Load or initialize the hash database
def load_hash_database():
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            return json.load(f)
    return {}

def save_hash_database(hash_data):
    with open(hash_file, "w") as f:
        json.dump(hash_data, f)

# Compute the hash of a file's content
def compute_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Index the codebase files
def index_codebase():
    # Load existing file hashes
    file_hashes = load_hash_database()

    # Create a copy of the current hashes to update
    updated_hashes = file_hashes.copy()

    for root, dirs, files in os.walk(codebase_directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".java"):
                file_path = os.path.join(root, file)
                file_hash = compute_file_hash(file_path)

                # Check if the file is new or has changed
                if file_path not in file_hashes or file_hashes[file_path] != file_hash:
                    print(f"Indexing file: {file_path}")

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()

                            # Process the file line by line
                            lines = code_content.split('\n')
                            for i, line in enumerate(lines):
                                if not line.strip():
                                    continue

                                # Generate embedding for the line
                                inputs = tokenizer(line, return_tensors="pt").to(device)
                                with torch.no_grad():
                                    outputs = model(**inputs)
                                    hidden_states = outputs.hidden_states[-1]  # Last layer
                                    embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

                                # Create document for Elasticsearch
                                doc = {
                                    "content": line.strip(),
                                    "file_path": file_path,
                                    "line_number": i + 1,
                                    "embedding": embedding,
                                }

                                # Index the document
                                es.index(index=index_name, body=doc)

                            # Update the hash after successful indexing
                            updated_hashes[file_path] = file_hash

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")

                else:
                    print(f"Skipping unchanged file: {file_path}")

    # Save merged hashes
    save_hash_database(updated_hashes)
    print("Indexing completed.")


# Run the indexing process
if __name__ == "__main__":
    try:
        index_codebase()
        resp = es.count(index="codebase_index")
        print("Number of indexed documents in codebase: " + str(resp["count"]))
    except Exception as e:
        print(f"Error during indexing: {e}")
