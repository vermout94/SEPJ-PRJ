import json
import os

import requests
import torch
from elasticsearch import Elasticsearch
from transformers import AutoTokenizer, AutoModel

# Initialize Elasticsearch
index_name = "codebase_index"
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "password")
)

# Load the model for embedding extraction
model_name = "BAAI/bge-base-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name).to(device)  # Use AutoModel, not AutoModelForCausalLM


# Function to get query embedding
def get_query_embedding(query):
    inputs = tokenizer(query, return_tensors="pt", truncation=True, max_length=512).to(device)
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
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding}
                }
            }
        }
    }

    # Execute search query
    try:
        response = es.search(index=index_name, body=search_query)
        hits = response['hits']['hits']
        return hits
    except Exception as e:
        print(f"Error: {e}")
        return None


# function to get all the questions from ../questions
def get_questions(p):
    questions = dict()
    for root, dirs, files in os.walk(p):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                code_snippet = file.split(".")[0]
                questions[code_snippet] = {"question": f.read().encode('utf-8').decode('unicode_escape')}
                questions[code_snippet]["answer"] = "./test_files/"+code_snippet+".py"
    return questions


def enumerate_text(text):7
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
    count_correct = 0
    count_incorrect = 0
    p_norm = "./questions/standard"  # standard questions
    p_llm = "./questions/llm"  # llm refined
    print("getting questions")
    questions = get_questions(p_norm)
    for q in questions:
        query = questions[q]["question"].strip()
        #print("Question: {}".format(query))
        hits = execute_search(query)
        if hits:
            print("Results: " + hits[0]["_source"]["content"])
            print("File Path: " + hits[0]["_source"]["file_path"])
            print("Expected: " + questions[q]["answer"])
            #rewriting the check, so that it checks if the correct answer is among the first three results
            print("Answer: " + questions[q]["answer"].strip())
            print(str(hits[0]["_source"]["file_path"].strip()))
            print(str(hits[0]["_score"]))
            is_correct = any(str(questions[q]["answer"].strip()) == str(hits[i]["_source"]["file_path"].strip()) for i in range(5))
            #print("Query result correct?\n" + str(is_correct))
            if is_correct:
                count_correct += 1
                enumerated_file = enumerate_text(hits[0]["_source"]["content"])
                print(enumerated_file)
                line = find_line(enumerated_file, query)
                print("Line: " + line)
            else:
                count_incorrect += 1


    #pint the number of correct and incorrect results
    print("Correct: {}\nIncorrect: {}".format(count_correct, count_incorrect))


