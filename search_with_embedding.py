import platform
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from elasticsearch import Elasticsearch

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# Loading the Hugging Face model
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, output_hidden_states=True).to(device)

def get_query_embedding(query):
    inputs = tokenizer(query, return_tensors="pt").to(device)
    with torch.no_grad(): # no_grad() --> Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward().
                          # It will reduce memory consumption for computations that would otherwise have requires_grad=True.
        outputs = model(**inputs)
        # Extract logits or another tensor attribute
        # logits = outputs.logits
        # embedding = logits[0].detach().cpu().numpy().tolist()
        hidden_states = outputs.hidden_states[-1]  # Get the last layer hidden
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()

        del outputs
        # del logits

        if platform.system()=='Windows':

            torch.cuda.empty_cache()

        if platform.system()=='Darwin': # Darwin --> Mac
                                          # https://stackoverflow.com/questions/1854/how-to-identify-which-os-python-is-running-on

            torch.mps.empty_cache() # "mps" refers to "Metal Performance Shaders" which are available for Mac (Apple)
                                    # --> see: https://developer.apple.com/metal/pytorch/
        return embedding


es_user = 'elastic' #os.getenv('ES_USERNAME')
es_password = 'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')
es_host = "http://localhost:9200"
index_name = "codebase_index"
MAPPING_FILE = "custom_mapping.json"  # Mapping file

es_client = Elasticsearch(
    "https://localhost:9200",
    ca_certs=r".\http_ca.crt",
    basic_auth=(es_user, es_password)
)

query_embedding = get_query_embedding("x+y")

print(type(query_embedding))

query_embedding_str = str(query_embedding[0])

query_embedding_str_length = len(query_embedding_str)
print(query_embedding_str_length)

# print(query_embedding_str[1:50])
# print(query_embedding_str[-50:query_embedding_str_length-1])

print(query_embedding_str[:50])
print(query_embedding_str[-50:])

# query_embedding_str_as_vector = query_embedding_str[1:query_embedding_str_length-1]

#print(query_embedding)


# resp = es_client.search(index="codebase_index", body={ "query": {
#                                                            "script_score": {
#                                                               "query": {
#                                                                 "match_all": {}
#                                                               },
#                                                               "script": {
#                                                                 "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
#                                                                 "params": {
#                                                                   "query_vector": query_embedding[0]
#                                                                 }
#                                                               }
#                                                             }
#                                                         }
#                                                      })

resp = es_client.search(index="codebase_index", knn= {"field": "embedding",
                                                      "query_vector": query_embedding[0],
                                                      "k": 3,
                                                      "num_candidates": 10
                                                     })


# response_json = resp
#
# for hit in response_json['hits']['hits']:
#     file_path = hit['_source']['file_path']
#     content = hit['_source']['content']
#     line_number = hit['_source']['line_number']
#
#     print(f"File: {file_path}, Line {line_number}: {content.strip()}")