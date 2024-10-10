import sys
import os
from elasticsearch import Elasticsearch


# Function to search the codebase using the provided query
def search_codebase(query, search_type="content"):
    es_user = os.getenv('ES_USERNAME')
    es_password = os.getenv('ES_PASSWORD')
    es = Elasticsearch(
        hosts=["http://localhost:9200"],
        http_auth=(es_user, es_password)
    )
    index_name = "codebase_index"

    # Search query based on the search type (content, function_name, class_name)
    if search_type == "function":
        search_field = "function_name"
    elif search_type == "class":
        search_field = "class_name"
    else:
        search_field = "content"

    # Elasticsearch search query
    search_query = {
        "query": {
            "match": {
                search_field: query
            }
        }
    }

    # Performing the search
    response = es.search(index=index_name, body=search_query)

    # Checking if hits exist and print results
    if response['hits']['total']['value'] > 0:
        for hit in response['hits']['hits']:
            file_path = hit['_source']['file_path']
            content = hit['_source']['content']
            line_number = hit['_source']['line_number']

            print(f"File: {file_path}, Line {line_number}: {content.strip()}")
    else:
        print("No matches found for your query.")


# Main execution
if __name__ == "__main__":
    # Ensuring the query and search type are passed as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: ./search_codebase.py '<query>' <search_type> (content|function|class)")
        sys.exit(1)

    # Getting the query and search type from the command-line arguments
    query = sys.argv[1]
    search_type = sys.argv[2]

    search_codebase(query, search_type)
