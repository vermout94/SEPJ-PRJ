import os
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


if __name__ == "__main__":
    count_correct = 0
    count_incorrect = 0
    p_norm = "./questions/standard"  # standard questions
    p_llm = "./questions/llm"  # llm refined
    print("getting questions")
    questions = get_questions(p_llm)
    for q in questions:
        query = questions[q]["question"].strip()
        #print("Question: {}".format(query))
        hits = execute_search(query)
        if hits:
            #print("Results: " + hits[0]["_source"]["content"])
            #print("File Path: " + hits[0]["_source"]["file_path"])
            #print("Expected: " + questions[q]["answer"])
            #rewriting the check, so that it checks if the correct answer is among the first three results
            print("Answer: " + questions[q]["answer"].strip())
            print(str(hits[0]["_source"]["file_path"].strip()))
            print(str(hits[0]["_score"]))
            print(str(hits[1]["_source"]["file_path"].strip()))
            print(str(hits[1]["_score"]))
            print(str(hits[2]["_source"]["file_path"].strip()))
            print(str(hits[2]["_score"]))
            print(str(hits[3]["_source"]["file_path"].strip()))
            print(str(hits[3]["_score"]))
            print(str(hits[4]["_source"]["file_path"].strip()))
            print(str(hits[4]["_score"]))
            is_correct = any(str(questions[q]["answer"].strip()) == str(hits[i]["_source"]["file_path"].strip()) for i in range(5))
            #print("Query result correct?\n" + str(is_correct))
            if is_correct:
                count_correct += 1
            else:
                count_incorrect += 1


    #pint the number of correct and incorrect results
    print("Correct: {}\nIncorrect: {}".format(count_correct, count_incorrect))


