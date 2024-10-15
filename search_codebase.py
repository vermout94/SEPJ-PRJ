import sys
import os
import requests
from elasticsearch import Elasticsearch
import json
import re


#function to query local running llm and structure db query
def structure_query(query):
    api_url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    prompt = """You will take in the openly formulated text listed in three backticks and optimize it to use as a 
    query for an elasticsearch database. ´´´{}´´´. output the json payload for the get request Based on the input 
    text. you will not provide any additional text.""".format(query)
    data = {
        "prompt": prompt,
        "model": "llama3.2"  # Ensure the correct model name if it's different
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
    es_user = os.getenv('ES_USERNAME')
    es_password = os.getenv('ES_PASSWORD')
    es = Elasticsearch(
        hosts=["http://localhost:9200"],
        basic_auth=(es_user, es_password)
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

    if search_type == "llm":
        search_query = json.loads(structure_query(query))
    print(search_query)
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
    search_codebase("i am looking for code that prints numbers in a loop", "llm")
    """# Ensuring the query and search type are passed as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: ./search_codebase.py '<query>' <search_type> (content|function|class)")
        sys.exit(1)

    # Getting the query and search type from the command-line arguments
    query = sys.argv[1]
    search_type = sys.argv[2]

    search_codebase(query, search_type)
"""
