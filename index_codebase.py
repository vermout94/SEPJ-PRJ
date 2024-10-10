import os
import re
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch

index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
es_user = os.getenv('ES_USERNAME')
es_password = os.getenv('ES_PASSWORD')
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=(es_user, es_password)
)

# Loading the Hugging Face model
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

# Path to codebase
codebase_directory = "./test_files/"


# Regex to extract function and class names
def extract_metadata(code_content):
    function_names = re.findall(r"def ([\w_]+)\(", code_content)
    class_names = re.findall(r"class ([\w_]+)\(", code_content)
    return function_names, class_names


# Function to index codebase files
# Function to index the codebase
def index_codebase():
    for root, dirs, files in os.walk(codebase_directory):
        for file in files:
            # Add other file extensions as needed
            if file.endswith(".py") or file.endswith(".java"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                    function_names, class_names = extract_metadata(code_content)

                    # Index each line separately with metadata
                    lines = code_content.split('\n')
                    for i, line in enumerate(lines):
                        # Skip empty lines to avoid unnecessary processing
                        if not line.strip():
                            continue

                        # Tokenize and generate outputs
                        inputs = tokenizer(line, return_tensors="pt").to(device)
                        with torch.no_grad():
                            outputs = model(**inputs)
                            # Extract logits or another tensor attribute
                            logits = outputs.logits
                            embedding = logits[0].detach().cpu().numpy().tolist()
                            del outputs
                            del logits
                            torch.mps.empty_cache()

                        # Create document for Elasticsearch with the extracted embedding
                        doc = {
                            "content": line.strip(),
                            "file_path": file_path,
                            "function_name": function_names if function_names else None,
                            "class_name": class_names if class_names else None,
                            "line_number": i + 1,
                            "embedding": embedding
                        }

                        # Index document in Elasticsearch
                        es.index(index=index_name, body=doc)
                        print(f"Indexed {file_path}, line {i + 1}")


# Running the indexing process
if __name__ == "__main__":
    index_codebase()
