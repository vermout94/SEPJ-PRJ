import os
import subprocess
import time
import sys
import socket
from elasticsearch import Elasticsearch

# Configuration
ES_VERSION = "8.15.3"
ES_PORT = 9200
ES_HOST = f"http://localhost:{ES_PORT}"
INDEX_NAME = "codebase_index"
# Path to codebase
CODEBASE_DIR = "/path/to/codebase"
DOCKER_IMAGE = f"docker.elastic.co/elasticsearch/elasticsearch:{ES_VERSION}"
# Custom mapping of Elasticsearch
MAPPING_FILE = "custom_mapping.json"  # Mapping file


# Checking if a command exists
def command_exists(command):
    result = subprocess.run(f"command -v {command}", shell=True, stdout=subprocess.PIPE)
    return result.returncode == 0


# Installing Docker if it's not installed
def install_docker():
    if not command_exists("docker"):
        print("Docker not found. Installing Docker...")
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io"])
    else:
        print("Docker is already installed.")

# Check if port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Pulling and running Elasticsearch using Docker (https://hub.docker.com/_/elasticsearch)
def run_elasticsearch():
    if is_port_in_use(ES_PORT):
        print(f"Port {ES_PORT} is already in use. Assuming Elasticsearch is running.")
        return

    print(f"Pulling Elasticsearch image {DOCKER_IMAGE}...")
    subprocess.run(["docker", "pull", DOCKER_IMAGE])

    print("Running Elasticsearch...")
    subprocess.run([
        "docker", "run", "-d", "-p", f"{ES_PORT}:{ES_PORT}",
        "-e", "discovery.type=single-node",
        "-e", f"xpack.security.enabled=true",
        "-e", f"ELASTIC_PASSWORD={ELASTIC_PASSWORD}",
        "--name", "elasticsearch", DOCKER_IMAGE
    ])

    # Waiting for Elasticsearch to start
    print("Waiting for Elasticsearch to start...")
    for _ in range(20):
        if is_port_in_use(ES_PORT):
            print("Elasticsearch is running.")
            return
        time.sleep(5)
    print("Error: Elasticsearch did not start. Exiting.")
    sys.exit(1)

# Install required Python dependencies
def install_python_dependencies():
    print("Installing required Python libraries...")
    subprocess.run(["pip3", "install", "--upgrade", "elasticsearch"])


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

    print(f"Creating custom mapping for Elasticsearch index '{INDEX_NAME}'...")
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=mapping)
        print("Custom mapping created.")
    else:
        print(f"Index '{INDEX_NAME}' already exists. Skipping creation.")


# Main setup process
def main():
    install_docker()
    run_elasticsearch()
    install_python_dependencies()
    es = connect_to_elasticsearch()
    create_custom_mapping(es)
  #  run_indexing_script()

    print("Setup completed.")

if __name__ == "__main__":
    main()
