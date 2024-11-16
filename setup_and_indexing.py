import os
import subprocess
import time
import sys
import socket
from elasticsearch import Elasticsearch

# Configuration
ES_VERSION = "8.15.2"
ES_PORT = 9200
ES_HOST = f"http://localhost:{ES_PORT}"  # Use HTTP
INDEX_NAME = "codebase_index"
DOCKER_IMAGE = f"docker.elastic.co/elasticsearch/elasticsearch:{ES_VERSION}"
MAPPING_FILE = "custom_mapping.json"
ELASTIC_PASSWORD = "changeme"  # Replace with your desired password
OLLAMA_MODEL = "llama3.2"

# Check if a command exists
def command_exists(command):
    result = subprocess.run(f"command -v {command}", shell=True, stdout=subprocess.PIPE)
    return result.returncode == 0

# Install Docker if necessary
def install_docker():
    if not command_exists("docker"):
        print("Docker not found. Installing Docker...")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io"])
    else:
        print("Docker is already installed.")

# Install Ollama if necessary
def install_ollama():
    if not command_exists("ollama"):
        print("Ollama CLI not found. Please install it from the official website.")
        sys.exit(1)
    else:
        print("Ollama CLI is already installed.")

# Download Llama model if not available
def download_ollama_model():
    try:
        result = subprocess.run(["ollama", "pull", OLLAMA_MODEL], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Model {OLLAMA_MODEL} downloaded successfully.")
        else:
            print(f"Error downloading model {OLLAMA_MODEL}: {result.stderr}")
            sys.exit(1)
    except Exception as e:
        print(f"Exception while downloading model {OLLAMA_MODEL}: {e}")
        sys.exit(1)

# Check if Ollama server is running and start if necessary
def start_ollama_server():
    try:
        # Check if Ollama server is already running
        result = subprocess.run(["pgrep", "-f", "ollama serve"], stdout=subprocess.PIPE)
        if result.returncode != 0:  # Server not running
            print("Starting Ollama server...")
            subprocess.Popen(["ollama", "serve"])
            time.sleep(3)  # Give some time for the server to start
        else:
            print("Ollama server is already running.")
    except Exception as e:
        print(f"Error starting Ollama server: {e}")
        sys.exit(1)

# Check if port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Run Elasticsearch in Docker
def run_elasticsearch():
    if is_port_in_use(ES_PORT):
        print(f"Port {ES_PORT} is already in use. Please ensure it is available.")
        sys.exit(1)

    existing_container = subprocess.run(
        ["docker", "ps", "-q", "-f", "name=elasticsearch"], stdout=subprocess.PIPE, text=True
    ).stdout.strip()

    if existing_container:
        print("Elasticsearch container is already running.")
        return

    print(f"Pulling Elasticsearch image {DOCKER_IMAGE}...")
    subprocess.run(["docker", "pull", DOCKER_IMAGE])

    print("Running Elasticsearch...")
    subprocess.run([
        "docker", "run", "-d", "-p", f"{ES_PORT}:{ES_PORT}",
        "-e", "discovery.type=single-node",
        "-e", "xpack.security.enabled=true",
        "-e", f"ELASTIC_PASSWORD={ELASTIC_PASSWORD}",
        "--name", "elasticsearch", DOCKER_IMAGE
    ])

# Connect to Elasticsearch
def connect_to_elasticsearch():
    for attempt in range(20):
        try:
            es = Elasticsearch(
                [ES_HOST],
                basic_auth=("elastic", ELASTIC_PASSWORD),
                verify_certs=False
            )
            if es.ping():
                print("Connected to Elasticsearch")
                return es
            else:
                print(f"Attempt {attempt + 1}: Could not connect, retrying...")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Connection failed due to {e}, retrying...")

        time.sleep(3)

    print("Could not connect to Elasticsearch after multiple attempts.")
    sys.exit(1)

# Create a custom mapping in Elasticsearch
def create_custom_mapping(es):
    if not os.path.exists(MAPPING_FILE):
        print(f"Error: {MAPPING_FILE} not found.")
        sys.exit(1)

    with open(MAPPING_FILE, 'r') as file:
        mapping = file.read()

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"Custom mapping created for index '{INDEX_NAME}'.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

# Main setup process
def main():
    install_docker()
    run_elasticsearch()

    # Connect to Elasticsearch
    es = connect_to_elasticsearch()

    # Create custom mapping
    create_custom_mapping(es)

    # Install and start Ollama components
    install_ollama()
    download_ollama_model()
    start_ollama_server()

    print("Setup completed.")

if __name__ == "__main__":
    main()
