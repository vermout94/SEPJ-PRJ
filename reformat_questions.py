
import os
import time

import requests
import json
import re


def reformat_query(question):
    api_url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }

    prompt = """
   Write a Python code snippet according to the following context. Output only the code, without any comments, explanations, or extra text. Context:
    {}
    """.format(question)
    data = {
        "prompt": prompt,
        "model": "codellama:7b"
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
    question = "How can I use a list comprehension to extend a list in python?"
    #print(reformat_query(question))
    questions = dict()
    # reading in text files and passing it to the function
    for root, dirs, files in os.walk("./questions/standard"):
        for file in files:
            if file.endswith(".txt"):
                with open(os.path.join(root, file), 'r') as f:
                    code_snippet = file.split(".")[0]
                    questions[code_snippet] = {"question": f.read().encode('utf-8').decode('unicode_escape')}
                    questions[code_snippet]["answer"] = "./test_files/" + code_snippet + ".py"
    for key in questions:
        #q_new = reformat_query(questions[key]["question"])
        print(questions[key]["question"])
        q_new = reformat_query(questions[key]["question"])
        time.sleep(10)
        with open("./questions/llm/{}.txt".format(key), "x") as file:
            file.write(str(q_new))


