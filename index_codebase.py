import os
import hashlib
import json
import platform
import re
import subprocess
import sys
import time

from numpy.ma.core import squeeze


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

#install("elasticsearch")
#install("transformers")
#install("torch")
#install("huggingface_hub[cli]")

from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch

print("cuda is available: ", torch.cuda.is_available())

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
    request_timeout=60
)

# Loading the Hugging Face model
model_name = "Qwen/Qwen2.5-Coder-0.5B"
#"deepseek-ai/DeepSeek-Coder-V2-Lite-Base"
#"meta-llama/CodeLlama-7b-hf"
# #"codellama/CodeLlama-7b-hf"
# #"BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device) #, output_hidden_states=True

# Path to codebase
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

# Function to index codebase files
# Function to index the codebase
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
                    print(f"Indexing or updating file: {file_path}")

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()

                            # Process the file line by line
                            lines = code_content.split('\n')
                            for i, line in enumerate(lines):
                                if not line.strip():
                                    continue

                    # Tokenize and generate outputs
                    inputs = tokenizer(code_content, return_tensors="pt").to(device)
                    with torch.no_grad(): # no_grad() --> Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward().
                                          # It will reduce memory consumption for computations that would otherwise have requires_grad=True.
                        outputs = model(**inputs)

                        hidden_states = outputs.hidden_states[-1] # Get the last layer hidden
                        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

                        del outputs

                        if platform.system()=='Windows':

                            torch.cuda.empty_cache()

                        if platform.system()=='Darwin': # Darwin --> Mac
                                                          # https://stackoverflow.com/questions/1854/how-to-identify-which-os-python-is-running-on

                            torch.mps.empty_cache() # "mps" refers to "Metal Performance Shaders" which are available for Mac (Apple)
                                                    # --> see: https://developer.apple.com/metal/pytorch/
                                # Generate embedding for the line
                                inputs = tokenizer(line, return_tensors="pt").to(device)
                                with torch.no_grad():
                                    outputs = model(**inputs)
                                    hidden_states = outputs.hidden_states[-1]  # Last layer
                                    embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

                    # Create document for Elasticsearch with the extracted embedding
                    doc = {
                        "content": code_content,
                        "file_path": file_path,
                        "function_name": function_names if function_names else None,
                        "class_name": class_names if class_names else None,
                        "embedding": embedding
                    }

                                # Use file path and line number as unique ID
                                doc_id = f"{file_path}:{i + 1}"

                                # Index or overwrite the document
                                es.index(index=index_name, id=doc_id, body=doc)

                            # Update the hash after successful indexing
                            updated_hashes[file_path] = file_hash

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")

                else:
                    print(f"Skipping unchanged file: {file_path}")

    # Save merged hashes
    save_hash_database(updated_hashes)
    print("Indexing completed.")

# Running the indexing process
if __name__ == "__main__":
    try:
        index_codebase()
        resp = es.count(index="codebase_index")
        print("Number of indexed documents in codebase: " + str(resp["count"]))
    except Exception as e:
        print(f"Error during indexing: {e}")
