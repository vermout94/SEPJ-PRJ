import os
from elasticsearch import Elasticsearch

# Initialize Elasticsearch
index_name = "codebase_index"
#es_user = os.getenv('ES_USERNAME')
#es_password = os.getenv('ES_PASSWORD')
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "password")
)

# Delete all documents in the index
delete_query = {
    "query": {
        "match_all": {}
    }
}

try:
    response = es.delete_by_query(index=index_name, body=delete_query)
    print(f"Deleted {response['deleted']} documents from the index '{index_name}'.")
except Exception as e:
    print(f"Error: {e}")