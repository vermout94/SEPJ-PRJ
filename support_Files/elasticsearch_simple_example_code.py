from datetime import datetime

# from setup import connect_to_elasticsearch
#
# connect_to_elasticsearch()

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
#
# CERTIFICATE_PATH = f"elasticsearch:/usr/share/elasticsearch/config/certs/http_ca.crt"
# docker_command = ["docker", "cp", CERTIFICATE_PATH, f"./"]
# subprocess.run(docker_command, check=True)

es_password = os.getenv('ES_PASSWORD')
#es_password = 'Tf+yhOG=9Y-rWPGIuQaw'

print(es_password)

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

print("Elasticsearch info: ", es_client.info())
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

resp = es_client.search(index="codebase_index", query={"match_all": {}})
print("Got {} hits:".format(resp["hits"]["total"]["value"]))
for hit in resp["hits"]["hits"]:
    file_path = hit['_source']['file_path']
    #print(file_path)
    file_name = file_path.split("\\")[-1]
    print(file_name, ": ", hit["_source"]["function_name"])
    print(file_name, ": ", hit["_source"]["class_name"])

resp = es_client.count(index="codebase_lines_index")
print("Number of indexed lines in codebase: " + str(resp["count"]))

# resp = es_client.search(index="codebase_lines_index",
#                         query={ "match_all": {}})

# resp = es_client.search(index="codebase_lines_index",
#                         query={
#                                 "term": {
#                                     "function_name.keyword": "brake"
#                                 }
#                             })

resp = es_client.search(index="codebase_lines_index",
                        query={
                                "match": {
                                    "content": "Car"
                                }
                            })

print("Got {} hits:".format(resp["hits"]["total"]["value"]))
i=0
for hit in resp["hits"]["hits"]:
    file_path = hit['_source']['file_path']
    file_name = file_path.split("\\")[-1]
    line_number = hit['_source']['line_number']
    print(file_name, "Line ", line_number, "| content:", hit["_source"]["content"], "| function_name:", hit["_source"]["function_name"], "| class_name:", hit["_source"]["class_name"])
    # i = i +1
    # if i == 100:
    #     break
#
# hit = resp["hits"]["hits"][1000]
# file_path = hit['_source']['file_path']
# file_name = file_path.split("\\")[-1]
# line_number = hit['_source']['line_number']
#
# print(file_name, "Line ", line_number,  "| function_name:", hit["_source"]["function_name"], "| class_name:", hit["_source"]["class_name"])

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
#
# es_client.indices.delete(index="codebase_index")
# es_client.indices.delete(index="codebase_lines_index")

######################
# !!! DELETE ALL DOCUMENTS OF INDEX !!!
#
# es_client.delete_by_query(
#     index="codebase_index",
#     query={"match_all": {}}
# )
#
# es_client.delete_by_query(
#     index="codebase_lines_index",
#     query={"match_all": {}}
# )

# client.indices.refresh(index="test-index")
#
# resp = client.search(index="test-index", query={"match_all": {}})
# print("Got {} hits:".format(resp["hits"]["total"]["value"]))
# for hit in resp["hits"]["hits"]:
#     print("{timestamp} {author} {text}".format(**hit["_source"]))