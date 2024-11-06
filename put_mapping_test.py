from elasticsearch import Elasticsearch

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

print(es_client.info())

# trying to update mapping
resp = es_client.indices.create(index=index_name,
                                mappings={
                                            "properties": {
                                              "content": {
                                                "type": "text"
                                              },
                                              "file_path": {
                                                "type": "keyword"
                                              },
                                              "function_name": {
                                                "type": "text"
                                              },
                                              "class_name": {
                                                "type": "text"
                                              },
                                              "line_number": {
                                                "type": "integer"
                                              },
                                              "embedding": {
                                                "type": "dense_vector",
                                                "dims": 768
                                              }
                                            }
                                          }
)

print(resp)