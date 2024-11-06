from datetime import datetime

import subprocess
import sys

# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#
# install("elasticsearch")

from elasticsearch import Elasticsearch

#client = Elasticsearch("http://localhost:9200/", api_key="YOUR_API_KEY")

#client = Elasticsearch("http://localhost:9200")

es_user = 'elastic' #os.getenv('ES_USERNAME')
es_password = 'YJZ-7Vi-h_Xyv0v=R-jJ' #os.getenv('ES_PASSWORD')

# You need to pass the username and password to the Elasticsearch object as shown below:

# es_client = Elasticsearch(['http://localhost:9200'], basic_auth=(es_user, es_password))
# es_client = Elasticsearch(hosts="http://elastic:QBSb_3jAgZOd_QRd00nZ@localhost:9200/")

from elasticsearch import Elasticsearch

# Adds the HTTP header 'Authorization: Basic <base64 username:password>'
es_client = Elasticsearch(
    "https://localhost:9200",
    ca_certs=r".\http_ca.crt",
    basic_auth=(es_user, es_password)
)

# es_client = Elasticsearch(
#     hosts=["http://localhost:9200"],
#     http_auth=("elastic", "password")
# )

print(es_client.info())

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
#
# resp = es_client.get(index="test-index", id=1)
# print(resp["_source"])

resp = es_client.count(index="codebase_index")
print("Number of indexed lines: " + str(resp["count"]))


resp = es_client.search(index="codebase_index", body={"query": {"match": {"content":"x+y"}}})

response_json = resp

for hit in response_json['hits']['hits']:
    file_path = hit['_source']['file_path']
    content = hit['_source']['content']
    line_number = hit['_source']['line_number']

    print(f"File: {file_path}, Line {line_number}: {content.strip()}")

#print(resp["_source"]["content"])

# es_client.indices.delete(index="codebase_index")

# client.indices.refresh(index="test-index")
#
# resp = client.search(index="test-index", query={"match_all": {}})
# print("Got {} hits:".format(resp["hits"]["total"]["value"]))
# for hit in resp["hits"]["hits"]:
#     print("{timestamp} {author} {text}".format(**hit["_source"]))