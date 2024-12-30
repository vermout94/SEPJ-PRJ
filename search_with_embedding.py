import platform
import os
import re

import subprocess
import sys

from sympy.strategies.core import switch
# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#
# install("transformers")
# install("torch")

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from elasticsearch import Elasticsearch

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# Loading the Hugging Face model
model_name = "BAAI/bge-base-en-v1.5" #"Qwen/Qwen2.5-Coder-0.5B" #"BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)

def get_query_embedding(query):
    inputs = tokenizer(query, return_tensors="pt").to(device)
    with torch.no_grad(): # no_grad() --> Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward().
                          # It will reduce memory consumption for computations that would otherwise have requires_grad=True.
        outputs = model(**inputs)

        hidden_states = outputs.hidden_states[-1]  # Get the last layer hidden
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

        del outputs

        if platform.system()=='Windows':

            torch.cuda.empty_cache()

        if platform.system()=='Darwin': # Darwin --> Mac
                                          # https://stackoverflow.com/questions/1854/how-to-identify-which-os-python-is-running-on

            torch.mps.empty_cache() # "mps" refers to "Metal Performance Shaders" which are available for Mac (Apple)
                                    # --> see: https://developer.apple.com/metal/pytorch/
        return embedding


es_user = 'elastic' #os.getenv('ES_USERNAME')
es_password = os.getenv('ES_PASSWORD') #'e3eIx+qCdwGykhuLnjcP' #'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')
es_host = "http://localhost:9200"
index_name = "codebase_index"
lines_index_name = "codebase_lines_index"
#tmp_index_name = "tmp_idx"
MAPPING_FILE = "custom_mapping.json"  # Mapping file

es_client = Elasticsearch(
    "https://localhost:9200",
    basic_auth=(es_user, es_password),
    ca_certs=r".\http_ca.crt"
    #verify_certs=False
)

search_embedding = get_query_embedding("braking the tram")

# print(type(search_embedding))
# print("Length of embedding to search for: ", len(search_embedding))
# search_embedding_str = str(search_embedding[0])
# search_embedding_str_length = len(search_embedding_str)
# print(search_embedding_str_length)
# print(search_embedding_str[1:50])
# print(search_embedding_str[-50:query_embedding_str_length-1])
# print(search_embedding_str[:50])
# print(search_embedding_str[-50:])
# search_embedding_str_as_vector = search_embedding_str[1:search_embedding_str_length-1]
# print(search_embedding)

def print_resp(resp, mode):

    #print("Type of response: ", type(resp))
    print("Number of hits: ", len(resp['hits']['hits']) )

    response_json = resp

    for hit in response_json['hits']['hits']:
        file_path = hit['_source']['file_path']
        file_name = file_path.split("\\")[-1]
        file_score = hit['_score']
        print("==================")
        print(f"File: {file_path}, Score: {file_score}")

        #index_file_lines(file_path, tmp_index_name)

        # searching lines of each file
        if mode == "similarity":
            line_search_resp = lines_similarity_search(lines_index_name, file_path, search_embedding)
        elif mode == "knn":
            line_search_resp = lines_knn_search(lines_index_name, file_path, search_embedding)
        else:
            print("Unknown mode!")
            return

        if line_search_resp['hits']['total']['value'] > 0:
            print("Most Relevant Lines:")
            for hit in line_search_resp['hits']['hits']:
                content = hit['_source']['content']
                line_number = hit['_source']['line_number']
                line_score = hit['_score']
                print(f"{file_name}, Line {line_number}, Score: {line_score}, Content: {content.strip()}")
        else:
            print("No relevant lines found!")

        #es_client.indices.delete(index=tmp_index_name)

# vector search based on similarity of indexed embedding vectors
def similarity_search(idx_name, query_embedding):
    return es_client.search(index=idx_name, body={ "size":"3", #returns only top 3 hits!
                                                    "query": {
                                                               "script_score": {
                                                                  "query": {
                                                                    "match_all": {}
                                                                  },
                                                                  "script": {
                                                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                                                    "params": {
                                                                      "query_vector": query_embedding
                                                                    }
                                                                  }
                                                                }
                                                            }
                                                         })

def lines_similarity_search(idx_name, file_path, query_embedding):
    return es_client.search(index=idx_name, body={ "size":"3", #returns only top 3 hits!
                                                    "query": {
                                                               "script_score": {
                                                                  "query": {
                                                                    "match": {"file_path": file_path}
                                                                  },
                                                                  "script": {
                                                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                                                    "params": {
                                                                      "query_vector": query_embedding
                                                                    }
                                                                  }
                                                                }
                                                            }
                                                         })

# vector search based on k nearest neighbours of indexed embedding vectors
def knn_search(idx_name, query_embedding):
    return es_client.search(index=idx_name, knn= {"field": "embedding",
                                                  "query_vector": query_embedding,
                                                  "k": 3,
                                                  "num_candidates": 3
                                                 })

def lines_knn_search(idx_name, file_path, query_embedding):
    return es_client.search(index=idx_name, knn= {"field": "embedding",
                                                  "query_vector": query_embedding,
                                                  "k": 3,
                                                  "num_candidates": 3,
                                                  "filter" : [ {"match": {"file_path": file_path}} ]
                                                 })

resp = similarity_search(index_name, search_embedding)
print("\nResult of vector search based on similarity:")
print_resp(resp, "similarity")

resp = knn_search(index_name, search_embedding)
print("\nResult of vector search based on knn:")
print_resp(resp, "knn")












# def index_file_lines(file_path, idx_name):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         code_content = f.read()
#
#         # Index each line separately with metadata
#         lines = code_content.split('\n')
#         for i, line in enumerate(lines):
#             # Skip empty lines to avoid unnecessary processing
#             if not line.strip():
#                 continue
#
#             # Tokenize and generate outputs
#             inputs = tokenizer(line, return_tensors="pt").to(device)
#             with torch.no_grad(): # no_grad() --> Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward().
#                                   # It will reduce memory consumption for computations that would otherwise have requires_grad=True.
#                 outputs = model(**inputs)
#                 hidden_states = outputs.hidden_states[-1] # Get the last layer hidden
#                 embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()
#
#                 del outputs
#
#                 if platform.system()=='Windows':
#
#                     torch.cuda.empty_cache()
#
#                 if platform.system()=='Darwin': # Darwin --> Mac
#                                                   # https://stackoverflow.com/questions/1854/how-to-identify-which-os-python-is-running-on
#
#                     torch.mps.empty_cache() # "mps" refers to "Metal Performance Shaders" which are available for Mac (Apple)
#                                             # --> see: https://developer.apple.com/metal/pytorch/
#
#             # Create document for Elasticsearch with the extracted embedding
#             doc = {
#                 "content": line.strip(),
#                 "file_path": file_path,
#                 "line_number": i + 1,
#                 "embedding": embedding
#             }
#
#             # Index document in Elasticsearch
#             # print("Indexing file: ", file_path + ' | line: ' + str(i))
#             # print("Length of embedding: ", len(embedding))
#             es_client.index(index=idx_name, body=doc)