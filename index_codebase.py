import os
import re
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch
es = Elasticsearch(hosts=["http://localhost:9200"])
index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# Loading the Hugging Face model
# Model we use: codellama 7b / parameters: 6.74B / size: 3.8GB (https://ollama.com/library/codellama)
model_name = "codellama/CodeLlama-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Path to codebase
codebase_directory = "/path/to/codebase"


# Regex to extract function and class names
def extract_metadata(code_content):
    function_names = re.findall(r"def ([\w_]+)\(", code_content)
    class_names = re.findall(r"class ([\w_]+)\(", code_content)
    return function_names, class_names


# Function to index codebase files
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
                        inputs = tokenizer(line, return_tensors="pt")
                        outputs = model(**inputs)

                        # Creating document for Elasticsearch with custom mapping
                        doc = {
                            "content": line.strip(),
                            "file_path": file_path,
                            "function_name": function_names if function_names else None,
                            "class_name": class_names if class_names else None,
                            "line_number": i + 1,
                            "embedding": outputs.last_hidden_state.detach().numpy().tolist()
                        }

                        # Index document in Elasticsearch
                        es.index(index=index_name, body=doc)
                        print(f"Indexed {file_path}, line {i + 1}")


# Running the indexing process
if __name__ == "__main__":
    index_codebase()
