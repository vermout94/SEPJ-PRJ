import sys
import os
import requests
from elasticsearch import Elasticsearch
import json
import re


#function to query local running llm and structure db query
def structure_query(query):
    print(query)
    api_url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    prompt = """
        You will take in the openly formulated text listed in three backticks and optimize it to use as a 
        query for an elasticsearch database. ```{}```. output the json payload for the get request Based on the input 
        text. you will not provide any additional text.

        The query follows the following structure, your content will be placed in the space between the double backticks:

        {{
          "query": {{
            "match": {{
              "content": ```` 
            }}
          }},
          "_source": ["file_path", "content", "line_number"],
          "size": 10
        }}
    """.format(query)

    data = {
        "prompt": prompt,
        "model": "llama3.2"
    }

    try:
        response = requests.post(api_url, json=data, headers=headers)
        # Check if response status is OK
        if response.status_code == 200:
            try:
                # Split the response into multiple JSON objects
                responses = response.text.strip().split('\n')

                # Extract and concatenate the `response` field from each JSON object
                full_response = ''
                for res in responses:
                    json_data = json.loads(res)
                    full_response += json_data.get('response', '')
                #regex to ensure only json format will be returned:
                json_re = re.search(r'{.*}', full_response, re.DOTALL)
                if json_re:
                    json_response = json_re.group(0)
                    return json_response  # Return the cleaned-up response text
                else:
                    return None
            except requests.exceptions.JSONDecodeError as e:
                # Log the error and raw response text for debugging
                print(f"JSON Decode Error: {e}")
                print(f"Response text: {response.text}")
                return None

    except requests.exceptions.RequestException as e:
        #Catch any other errors (e.g., connection errors)
        print(f"Request failed: {e}")
        return None


# Function to search the codebase using the provided query
def search_codebase(query, search_type="content"):
    es_user = 'elastic' #os.getenv('ES_USERNAME')
    es_password = 'QBSb_3jAgZOd_QRd00nZ' #os.getenv('ES_PASSWORD')
    es_host = "http://localhost:9200"
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

    if search_type == "llm":
        search_query = structure_query(query)
        print(search_query)
        search_query = json.loads(search_query)
        print("the query:\n")
        print(search_query)

    # Convert search query to JSON string
    search_query_json = json.dumps(search_query)

    # Perform the search using a GET request
    response = requests.get(
        f"{es_host}/{index_name}/_search",
        headers={"Content-Type": "application/json"},
        auth=("elastic", "password"),
        data=search_query_json
    )

    # Check if the response status is OK
    if response.status_code == 200:
        response_json = response.json()
        print(response_json["hits"])
        # Checking if hits exist and print results
        if response_json['hits']['total']['value'] > 0:
            for hit in response_json['hits']['hits']:
                file_path = hit['_source']['file_path']
                content = hit['_source']['content']
                line_number = hit['_source']['line_number']

                print(f"File: {file_path}, Line {line_number}: {content.strip()}")
        else:
            print("No matches found for your query.")
    else:
        print(f"Search request failed: {response.status_code}, {response.text}")


# Main execution
if __name__ == "__main__":
    search_codebase("code that prints numbers in a loop", "llm")
    """# Ensuring the query and search type are passed as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: ./search_codebase.py '<query>' <search_type> (content|function|class)")
        sys.exit(1)

    # Getting the query and search type from the command-line arguments
    query = sys.argv[1]
    search_type = sys.argv[2]

    search_codebase(query, search_type)
"""
