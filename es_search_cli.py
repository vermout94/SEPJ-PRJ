import re
import json
import os
import requests
import torch
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModel, AutoModelForSeq2SeqLM

# Initialize Elasticsearch
index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "password")
)

# Load the model for embedding extraction
#model_name = "BAAI/bge-base-en-v1.5"
model_name = "EleutherAI/gpt-neo-1.3B"
# model_name = "Qwen/Qwen2.5-Coder-0.5B"
# model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Base"
# model_name = "meta-llama/CodeLlama-7b-hf"
# model_name = "codellama/CodeLlama-7b-hf"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)  # Use AutoModel, not AutoModelForCausalLM
#model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

# Function to get query embedding
def get_query_embedding(query):
    inputs = tokenizer(query, return_tensors="pt", truncation=True, max_length=1024).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        hidden_states = outputs.last_hidden_state  # Use hidden states
        embedding = hidden_states.mean(dim=1).squeeze().cpu().numpy().tolist()  # Mean pooling
    return embedding


def execute_search(query):
    # Generate query embedding
    query_embedding = get_query_embedding(query)

    # Elasticsearch search query using script_score with cosine similarity
    search_query = {
        "field": "embedding",
         "query_vector": query_embedding,
         "k": 3,
         "num_candidates": 3
         }

    # Execute search query
    try:
        response = es.search(
            index=index_name,
            body={
                "knn": {
                    "field": "embedding",  # The dense vector field
                    "query_vector": query_embedding,  # Your query embedding
                    "k": 5,  # Number of nearest neighbors to retrieve
                    "num_candidates": 50  # Number of candidates to consider for kNN
                },
                "query": {
                    "bool": {
                        "should": [
                            # Full-text search on the content field
                            {
                                "match": {
                                    "content": query  # The text you're searching for
                                }
                            }
                        ]
                    }
                }
            }
        )

        hits = response['hits']['hits']
        return hits
    except Exception as e:
        print(f"Error: {e}")
        return None


def enumerate_text(text):
    lines = text.split("\n")
    new_lines = ""
    for i, line in enumerate(lines):
        new_lines += f"#{i+1}: {line}\n"
    return new_lines


def find_line(text, question):
    prompt = f"""
    you will be provided with a multiline text. 
    The lines are enumerated starting from 1. 
    your task is to find the row that is closest to the question. 
    The question is: {question}. 
    Do not output any code. 
    just provide the line number marked with a pound sign in the provided context. 
    the context is:
    {text}
    """
    api_url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "model": "llama3.2:latest"
    }
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
                if 'response' in json_data:
                    full_response += json_data['response']
                else:
                    print(f"Warning: 'response' field not found in JSON object: {json_data}")
            return full_response
        except json.JSONDecodeError as e:
            # Log the error and raw response text for debugging
            print(f"JSON Decode Error: {e}")
            print(f"Response text: {response.text}")
            return None
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None


if __name__ == "__main__":
    while True:
        # Get question input from user
        query = input("Enter your question (or type 'exit' to quit): ").strip()
        if query.lower() == "exit":
            print("Exiting the program.")
            break

        # Execute search
        hits = execute_search(query)
        if hits:
            # Use only the first result
            first_hit = hits[0]
            second_hit = hits[1]
            third_hit = hits[2]
            fourth_hit = hits[3]
            fifth_hit = hits[4]
            print("1: " + first_hit["_source"]["file_path"])
            print("2: " + second_hit["_source"]["file_path"])
            print("3: " + third_hit["_source"]["file_path"])
            print("4: " + fourth_hit["_source"]["file_path"])
            print("5: " + fifth_hit["_source"]["file_path"])
            search_selection = input("Enter the number corresponding to the file to continue searching (1/2/3): ")

            if search_selection == "1":
                first_hit=first_hit
            if search_selection == "2":
                first_hit = second_hit
            if search_selection == "3":
                first_hit = third_hit
            if search_selection == "4":
                first_hit = fourth_hit
            if search_selection == "5":
                first_hit = fifth_hit

            print("Results: " + first_hit["_source"]["content"])
            print("File Path: " + first_hit["_source"]["file_path"])
            enumerated_file = enumerate_text(first_hit["_source"]["content"])
            #print("Enumerated File:\n" + enumerated_file)

            # Find the closest line in the text
            line = find_line(enumerated_file, query)
            print("Line: " + line)
            #regex to isolate number
            line_number = int(re.search(r'\d+', line).group())

            #print line -5 to line +10
            print("Found code snippet:")
            lines = enumerated_file.split("\n")
            for i in range(max(0, line_number - 5), min(len(lines), line_number + 10)):
                print(lines[i])
        else:
            print("No results found.")
