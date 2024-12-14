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
    http_auth=("elastic", "password")
)

# Loading the Hugging Face model
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)

# Path to codebase
codebase_directory = "./test_files/"


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
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                    function_names, class_names = extract_metadata(code_content)

                    #lines = code_content.split('\n')
                    print(code_content)
                    lines = code_content.strip()
                    print(lines)

                    # Get embedding
                    embedding = get_embedding(lines)

                    # Confirm embedding dimensions are as expected (e.g., 768)
                    #print("Embedding dimensions:", len(embedding))

                    # Create document for Elasticsearch
                    doc = {
                        #"content": line.strip(),
                        "content": lines,
                        "file_path": file_path,
                        "function_name": function_names if function_names else None,
                        "class_name": class_names if class_names else None,
                        "code_len": len(lines),
                        "embedding": embedding
                    }

                    # Index document in Elasticsearch
                    es.index(index=index_name, body=doc)
                    print(f"Indexed {file_path}, lines {len(lines)}")


# Running the indexing process
if __name__ == "__main__":
    index_codebase()
