import json

from sentence_transformers import SentenceTransformer,util
model = SentenceTransformer('all-mpnet-base-v2')

embedding = 'who is the best player in the world'

query_embedding = model.encode(embedding, convert_to_tensor=True)

print("Length of embedding vector: ", len(query_embedding))

print(query_embedding[:5])

# # Create a dictionary with the text_data
# json_data = {"text": embedding, "embedding": query_embedding.tolist()}
#
# # Convert the dictionary to a JSON-formatted string
# json_string = json.dumps(json_data, indent=2)
#
# # Print the JSON string
# print(json_string)