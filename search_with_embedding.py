from index_codebase import get_embedding as get_query_embedding, es as es_client, index_name, lines_index_name

def print_resp(resp, search_embedding, lines_search_mode):

    print("Number of hits: ", len(resp['hits']['hits']) )

    response_json = resp

    for hit in response_json['hits']['hits']:
        file_path = hit['_source']['file_path']

        file_score = hit['_score']
        print("==================")
        print(f"File: {file_path}, Score: {file_score}")

        # searching lines of each file
        if lines_search_mode == "similarity":
            line_search_resp = lines_similarity_search(lines_index_name, file_path, search_embedding)
        elif lines_search_mode == "knn":
            line_search_resp = lines_knn_search(lines_index_name, file_path, search_embedding)
        else:
            print("Unknown mode!")
            return

        print_line_search_resp(line_search_resp)

def print_line_search_resp(line_search_resp, print_file_path=False):
    if line_search_resp['hits']['total']['value'] > 0:
        print("Most Relevant Lines:")
        for hit in line_search_resp['hits']['hits']:
            content = hit['_source']['content']
            file_path = hit['_source']['file_path']
            file_name = file_path.split("\\")[-1]
            line_number = hit['_source']['line_number']
            line_score = hit['_score']
            if line_score > 0:
                if print_file_path:
                    print("File: ", file_path)
                print(f"Line {line_number}, Score: {line_score}, Content: {content.strip()}")
    else:
        print("No relevant lines found!")

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
                                                                    "term": {"file_path.keyword": file_path}
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

# vector search based on k nearest neighbours of indexed embedding vectors combined with full-text search
def knn_combined_search(idx_name, query_embedding, search_input):
    return es_client.search(index=idx_name,
                            body={
                                "knn": {
                                    "field": "embedding",  # The dense vector field
                                    "query_vector": query_embedding,  # Your query embedding
                                    "k": 3,  # Number of nearest neighbors to retrieve
                                    "num_candidates": 3  # Number of candidates to consider for kNN
                                },
                                "query": {
                                    "bool": {
                                        "should": [
                                            # Full-text search on the content field
                                            {
                                                "match": {
                                                    "content": search_input  # The text you're searching for
                                                }
                                            }
                                        ]
                                    }
                                },
                                "size": 3
                            }
                            )

def lines_knn_function_search(idx_name, query_embedding):
    return es_client.search(index=idx_name, knn={"field": "embedding",
                                                 "query_vector": query_embedding,
                                                 "k": 3,
                                                 "num_candidates": 3,
                                                 "filter": [{"term": {"function_name.keyword": "function"}}]
                                                 })

def lines_knn_class_search(idx_name, query_embedding):
    return es_client.search(index=idx_name, knn={"field": "embedding",
                                                 "query_vector": query_embedding,
                                                 "k": 3,
                                                 "num_candidates": 3,
                                                 "filter": [{"term": {"class_name.keyword": "class"}}]
                                                 })

def lines_knn_search(idx_name, file_path, query_embedding):
    return es_client.search(index=idx_name, knn= {"field": "embedding",
                                                  "query_vector": query_embedding,
                                                  "k": 3,
                                                  "num_candidates": 3,
                                                  "filter" : [ {"term": {"file_path.keyword": file_path}} ]
                                                 })

def search_codebase(search_input, search_type):

    search_embedding = get_query_embedding(search_input)

    if search_type == "content":
        resp = knn_combined_search(index_name, search_embedding, search_input)
        print("\nResult of content search:")
        print_resp(resp, search_embedding, "knn")
    elif search_type == "function":
        resp = lines_knn_function_search(lines_index_name, search_embedding)
        print("\nResult of function search:")
        print_line_search_resp(resp, True)
    elif search_type == "class":
        resp = lines_knn_class_search(lines_index_name, search_embedding)
        print("\nResult of class search:")
        print_line_search_resp(resp, True)