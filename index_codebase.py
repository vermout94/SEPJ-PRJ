import os
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
device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
es_user = 'elastic' #os.getenv('ES_USERNAME')
es_password = 'e3eIx+qCdwGykhuLnjcP' #'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')
es_client = Elasticsearch(
    "https://localhost:9200",
    ca_certs=r".\http_ca.crt",
    basic_auth=(es_user, es_password),
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

                    # Index each file separately with metadata

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

                    # Create document for Elasticsearch with the extracted embedding
                    doc = {
                        "content": code_content,
                        "file_path": file_path,
                        "function_name": function_names if function_names else None,
                        "class_name": class_names if class_names else None,
                        "embedding": embedding
                    }

                    # Index document in Elasticsearch
                    print("Indexing file: " + file_path)

                    print("Length of embedding: ", len(embedding))
                    # print("Length of embedding first sub vector: ", len(embedding[0]))
                    # embedding_str = str(embedding[0])
                    # print(embedding_str[:10])
                    # embedding_str = str(embedding[1])
                    # print(embedding_str[:10])

                    #print(doc)
                    es_client.index(index=index_name, body=doc)
                    #print(f"Indexed {file_path}, line {i + 1}")

    time.sleep(5)

    resp = es_client.count(index=index_name)
    print("Number of indexed documents: " + str(resp["count"]))

# Running the indexing process
if __name__ == "__main__":
    index_codebase()
