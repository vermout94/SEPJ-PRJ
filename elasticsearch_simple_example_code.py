from datetime import datetime

import subprocess
import sys
import os

# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#
# install("elasticsearch")

from elasticsearch import Elasticsearch

#client = Elasticsearch("http://localhost:9200/", api_key="YOUR_API_KEY")

#client = Elasticsearch("http://localhost:9200")

es_password = os.getenv('ES_PASSWORD')

#print(es_password)

es_user = 'elastic' #os.getenv('ES_USERNAME')
#es_password = 'QBSb_3jAgZOd_QRd00nZ' # 'e3eIx+qCdwGykhuLnjcP' #'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')

# You need to pass the username and password to the Elasticsearch object as shown below:

es_client = Elasticsearch(
    "https://localhost:9200",
    basic_auth=(es_user, es_password),
    ca_certs=r".\http_ca.crt"
    #verify_certs=False
)

if es_client.ping():
    print("Connected to Elasticsearch")

print("Elasticseach info: ", es_client.info())
print("Indices in database: ", list(es_client.indices.get(index="*").keys()))

# link to documentation of class for elasticsearch client
# https://elasticsearch-py.readthedocs.io/en/v8.15.1/api/elasticsearch.html

# for block comment use ctrl + / (numpad)
#
# doc = {
#     "author": "kimchy",
#     "text": "Elasticsearch: cool. bonsai cool.",
#     "timestamp": datetime.now(),
# }
#
# resp = es_client.index(index="test-index", id=1, document=doc)
# print(resp["result"])

# resp = es_client.count(index="test-index")
# print("Number of indexed documents: " + str(resp["count"]))

# resp = es_client.get(index="test-index", id=1)
# print("Source of indexed document with id=1: " + str(resp["_source"]))
#
resp = es_client.count(index="codebase_index")
print("Number of indexed documents in codebase: " + str(resp["count"]))

# standard query for full text search

# resp = es_client.search(index="codebase_index", body={"query": {"match": {"content":"x+y"}}})
#
# response_json = resp
#
# for hit in response_json['hits']['hits']:
#     file_path = hit['_source']['file_path']
#     content = hit['_source']['content']
#     line_number = hit['_source']['line_number']
#
#     print(f"File: {file_path}, Line {line_number}: {content.strip()}")

#print(resp["_source"]["content"])

######################
# !!! DELETE INDEX !!!

#es_client.indices.delete(index="codebase_index")

# client.indices.refresh(index="test-index")
#
# resp = client.search(index="test-index", query={"match_all": {}})
# print("Got {} hits:".format(resp["hits"]["total"]["value"]))
# for hit in resp["hits"]["hits"]:
#     print("{timestamp} {author} {text}".format(**hit["_source"]))