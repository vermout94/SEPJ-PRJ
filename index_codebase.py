import os
import platform
import re
import subprocess
import sys

from numpy.ma.core import squeeze


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# install("elasticsearch")
# install("transformers")
# install("torch")

from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initializing Elasticsearch

index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
es_user = 'elastic' #os.getenv('ES_USERNAME')
es_password = 'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')
es_client = Elasticsearch(
    "https://localhost:9200",
    ca_certs=r".\http_ca.crt",
    basic_auth=(es_user, es_password),
    request_timeout=60
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
                        with torch.no_grad(): # no_grad() --> Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward().
                                              # It will reduce memory consumption for computations that would otherwise have requires_grad=True.
                            outputs = model(**inputs)
                            # Extract logits or another tensor attribute
                            #logits = outputs.logits
                            #embedding = logits[0].detach().cpu().numpy().tolist()
                            hidden_states = outputs.hidden_states[-1] # Get the last layer hidden
                            embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

                            del outputs
                            #del logits

                            if platform.system()=='Windows':

                                torch.cuda.empty_cache()

                            if platform.system()=='Darwin': # Darwin --> Mac
                                                              # https://stackoverflow.com/questions/1854/how-to-identify-which-os-python-is-running-on

                                torch.mps.empty_cache() # "mps" refers to "Metal Performance Shaders" which are available for Mac (Apple)
                                                        # --> see: https://developer.apple.com/metal/pytorch/

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
                        print(file_path + ' | line: ' + str(i))

                        print("Length of embedding: ", len(embedding))
                        # print("Length of embedding first sub vector: ", len(embedding[0]))
                        # embedding_str = str(embedding[0])
                        # print(embedding_str[:10])
                        # embedding_str = str(embedding[1])
                        # print(embedding_str[:10])

                        #print(doc)
                        es_client.index(index=index_name, body=doc)
                        #print(f"Indexed {file_path}, line {i + 1}")

    resp = es_client.count(index=index_name)
    print("Number of indexed lines: " + str(resp["count"]))

# Running the indexing process
if __name__ == "__main__":
    index_codebase()
