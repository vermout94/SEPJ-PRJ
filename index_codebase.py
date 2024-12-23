import hashlib
import os
import re
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch

index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
es_user = os.getenv('ES_USERNAME', 'elastic')
es_password = os.getenv('ES_PASSWORD', 'password')
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    basic_auth=(es_user, es_password),
    verify_certs=False,
)

# Loading the Hugging Face model you want to use
model_name = "BAAI/bge-base-en-v1.5"
# model_name = "Qwen/Qwen2.5-Coder-0.5B"
# model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Base"
# model_name = "meta-llama/CodeLlama-7b-hf"
# model_name = "codellama/CodeLlama-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)

# Path to codebase
codebase_directory = os.path.abspath("./test_files/")

# Compute the hash of a file's content
def compute_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_doc_id(file_path, file_hash):
    """Generate a consistent document ID based on file path and hash."""
    unique_id = f"{file_path}:{file_hash}".encode("utf-8")
    return hashlib.md5(unique_id).hexdigest()


# Regex to extract function and class names
def extract_metadata(code_content):
    function_names = re.findall(r"def ([\w_]+)\(", code_content)
    class_names = re.findall(r"class ([\w_]+)\(", code_content)
    return function_names, class_names


def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt",max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        # Use hidden states and apply mean pooling
        hidden_states = outputs.hidden_states[-1]  # Get the last layer hidden states
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()  # Average across tokens
    return embedding


# Function to index codebase files
# Function to index the codebase
def index_codebase():
    for root, dirs, files in os.walk(codebase_directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".java") or file.endswith(".php"):
                file_path = os.path.join(root, file)
                file_hash = compute_file_hash(file_path)

                doc_id = compute_doc_id(file_path, file_hash)
                print(f"Generated doc_id for {file_path}: {doc_id}")

                try:
                    existing_doc = es.get(index=index_name, id=doc_id)
                    if existing_doc["_source"].get("file_hash") == file_hash:
                        print(f"Skipping unchanged file: {file_path}")
                        continue
                except Exception:
                    # Document does not exist, proceed with indexing
                    pass

                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                    function_names, class_names = extract_metadata(code_content)
                    #lines = code_content.split('\n')
                    #print(code_content)
                    lines = code_content.strip()
                    #print(lines)

                    # Get embedding
                    embedding = get_embedding(lines)

                    # Confirm embedding dimensions are as expected (e.g., 768)
                    #print("Embedding dimensions:", len(embedding))

                    # Create document for Elasticsearch
                    doc = {
                        "content": lines, # add hashing to lines = full doc content
                        "file_path": file_path,
                        "file_hash": file_hash,
                        "function_name": function_names if function_names else None,
                        "class_name": class_names if class_names else None,
                        "code_len": len(lines),
                        "embedding": embedding
                    }

                    # Index document in Elasticsearch
                    es.index(index=index_name, id=doc_id, body=doc)
                    print(f"Indexed {file_path}, lines {len(lines)}")


# Running the indexing process
if __name__ == "__main__":
    try:
        if not es.ping():
            raise ValueError("Elasticsearch is not running or accessible.")
        index_codebase()
        resp = es.count(index=index_name)
        print("Number of indexed documents in codebase: " + str(resp["count"]))
    except Exception as e:
        print(f"Error during indexing: {e}")