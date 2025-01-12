import hashlib
import os
import re
import time
import sys
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch
index_name = "codebase_index"
lines_index_name = "codebase_lines_index"

es_user = os.getenv('ES_USERNAME', 'elastic')
es_password = os.getenv('ES_PASSWORD', 'password')

es = Elasticsearch(
    hosts=["https://localhost:9200"],
    basic_auth=(es_user, es_password),
    ca_certs=r"./http_ca.crt",
    verify_certs=True
)

device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
# Loading the Hugging Face model you want to use
model_name = "BAAI/bge-base-en-v1.5"
# model_name = "Qwen/Qwen2.5-Coder-0.5B"
# model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Base"
# model_name = "meta-llama/CodeLlama-7b-hf"
# model_name = "codellama/CodeLlama-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)


# Compute the hash of a file's content
def compute_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compute_doc_id(file_path):
    """Generate a consistent document ID based on file path and hash."""
    unique_id = f"{file_path}".encode("utf-8")
    return hashlib.md5(unique_id).hexdigest()

# Regex to extract function and class names
def extract_metadata(code_content):
    function_names = re.findall(r"def ([\w_]+)\(", code_content)
    class_names = re.findall(r"class ([\w_]+):", code_content)
    return function_names, class_names

def get_embedding(text): # Tokenize and generate outputs
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        # Use hidden states and apply mean pooling
        hidden_states = outputs.hidden_states[-1]  # Get the last layer hidden states
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()  # Average across tokens
    return embedding

def indexing_by_file(file_path, file_hash, doc_id, idx_name, mode):
    with open(file_path, 'r', encoding='utf-8') as f:
        code_content = f.read()
        function_names, class_names = extract_metadata(code_content)
        code_content = code_content.strip()
        # Get embedding
        embedding = get_embedding(code_content)

        # Create document for Elasticsearch
        doc = {
            "content": code_content,  # add hashing to lines = full doc content
            "file_path": file_path,
            "file_hash": file_hash,
            "function_name": function_names if function_names else None,
            "class_name": class_names if class_names else None,
            "code_len": len(code_content),
            "embedding": embedding
        }

        # Index new document or update existing document
        if mode == "create":
            es.create(index=idx_name, id=doc_id, document=doc)
        elif mode == "update":
            es.update(index=idx_name, id=doc_id, doc=doc)

def indexing_by_line(file_path, idx_name):
    es.delete_by_query(
        index=idx_name,
        query={ "term": {"file_path.keyword": file_path} }
    )

    with open(file_path, 'r', encoding='utf-8') as f:
        code_content = f.read()

        print("Indexing lines...")
        # Index each line separately
        lines = code_content.split('\n')

        for i, line in enumerate(lines):
            # Skip empty lines to avoid unnecessary processing
            if not line.strip():
                continue

            function_names, class_names = extract_metadata(line)
            function_name = "function" if function_names else None
            class_name = "class" if class_names else None

            embedding = get_embedding(line)

            line_number = i + 1

            # Create document for Elasticsearch with the extracted embedding
            doc = {
                "content": line.strip(),
                "file_path": file_path,
                "function_name": function_name,
                "class_name": class_name,
                "line_number": line_number,
                "embedding": embedding
            }

            # Index a new document for each line
            es.index(index=idx_name, body=doc)

        print("Number of indexed lines: ", line_number)


def check_for_deleted_files(file_list):
    print("======================")
    print("Checking if files have been deleted...")

    search_response = es.search(
        index=index_name,
        query={"bool": {
                "must_not": [{
                    "terms": {
                        "file_path.keyword": file_list
                    }
                }]
            }
        }
    )

    num_of_deleted_files = search_response['hits']['total']['value']
    print("Number of files deleted from codebase:", num_of_deleted_files)

    if num_of_deleted_files > 0:
        print("Deleted files:")
        for h in search_response['hits']['hits']:
            print(h['_source']['file_path'])

        print("Deleting files from index...")
        delete_response = es.delete_by_query(
            index=index_name,
            query={"bool": {
                    "must_not": [{
                        "terms": {
                            "file_path.keyword": file_list
                        }
                    }]
                }
            }
        )

        print("Number of files deleted from index:", delete_response['deleted'])

        print("Deleting lines from index...")
        delete_response = es.delete_by_query(
            index=lines_index_name,
            query={"bool": {
                "must_not": [{
                    "terms": {
                        "file_path.keyword": file_list
                    }
                }]
            }
            }
        )

        print("Number of lines deleted from index:", delete_response['deleted'])

# Function to index codebase files
def index_codebase(codebase_directory):
    codebase_file_list = list()
    for root, dirs, files in os.walk(codebase_directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".java") or file.endswith(".php"):
                file_path = os.path.join(root, file)
                print("======================")
                print(f"Processing file: {file_path}")
                codebase_file_list.append(file_path)

                file_hash = compute_file_hash(file_path)

                doc_id = compute_doc_id(file_path)
                print(f"Generated doc_id: {doc_id}")

                print(f"Checking if a document exists in index...")

                if es.exists(index=index_name, id=doc_id):

                    print(f"A document already exists in index!")

                    existing_doc = es.get(index=index_name, id=doc_id)

                    print(f"Checking if the file has changed...")

                    if existing_doc["_source"].get("file_hash") == file_hash:
                        print(f"Hash value is the same - skipping unchanged file...")
                        continue
                    else:
                        print(f"Hash value is different - updating index for existing document...")

                        # Update existing document in Elasticsearch
                        indexing_by_file(file_path, file_hash, doc_id, index_name, "update")
                        # Indexing lines of the file in a separate index
                        indexing_by_line(file_path, lines_index_name)
                        print(f"Document updated successfully.")

                else:

                    print(f"No document for this file in index yet - creating a new document...")

                    # Index new document in Elasticsearch
                    indexing_by_file(file_path, file_hash, doc_id, index_name, "create")
                    # Indexing lines of the file in a separate index
                    indexing_by_line(file_path, lines_index_name)
                    print(f"Document indexed successfully.")

    check_for_deleted_files(codebase_file_list)


# Running the indexing process
if __name__ == "__main__":
    try:
        if not es.ping():
            raise ValueError("Elasticsearch is not running or accessible.")

        # Path to codebase
        try:
            codebase_directory = sys.argv[1]
        except IndexError:
            raise ValueError("Please provide the path to the codebase directory as an argument.")

        #check if path exists and is a directory
        if not os.path.exists(codebase_directory):
            raise ValueError(f"Directory does not exist: {codebase_directory}")
        if not os.path.isdir(codebase_directory):
            raise ValueError(f"Path is not a directory: {codebase_directory}")
        codebase_directory = os.path.abspath(codebase_directory)


        index_codebase(codebase_directory)
        time.sleep(3) # make sure that index is up-to-date before counting
        resp = es.count(index=index_name)
        print("\n======================")
        print("Number of indexed files from codebase: " + str(resp["count"]))
        resp = es.count(index=lines_index_name)
        print("\n======================")
        print("Number of indexed lines from codebase: " + str(resp["count"]))
    except Exception as e:
        print(f"Error during indexing: {e}")