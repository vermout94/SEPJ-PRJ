import os
import subprocess
import time
import sys
import socket
import platform
from elasticsearch import Elasticsearch

# Configuration
ES_VERSION = "8.15.3"
ES_PORT = 9200
ES_HOST = f"http://localhost:{ES_PORT}"
INDEX_NAME = "codebase_index"
LINES_INDEX_NAME = "codebase_lines_index"
DOCKER_IMAGE = f"docker.elastic.co/elasticsearch/elasticsearch:{ES_VERSION}"
MAPPING_FILE = "custom_mapping.json"
ELASTIC_PASSWORD = "password"

# Check platform
IS_WINDOWS = platform.system().lower() == "windows"

# Checking if a command exists
def command_exists(command):
    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return True
    except FileNotFoundError:
        return False

# Install Docker if not installed (Windows-specific adjustments)
def install_docker():
    if not command_exists("docker"):
        if IS_WINDOWS:
            print("Docker not found. Please install Docker Desktop for Windows manually.")
            sys.exit(1)
        else:
            print("Docker not found. Installing Docker...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io"], check=True)
    else:
        print("Docker is already installed.")

# Check if port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Run Elasticsearch using Docker
def run_elasticsearch():
    if is_port_in_use(ES_PORT):
        print(f"Port {ES_PORT} is already in use. Assuming Elasticsearch is running.")
        return

    print(f"Pulling Elasticsearch image {DOCKER_IMAGE}...")
    subprocess.run(["docker", "pull", DOCKER_IMAGE], check=True)

    print("Running Elasticsearch...")
    docker_command = [
        "docker", "run", "-d", "-p", f"{ES_PORT}:{ES_PORT}",
        "-e", "discovery.type=single-node",
        "-e", f"xpack.security.enabled=true",
        "-e", f"ELASTIC_PASSWORD={ELASTIC_PASSWORD}",
        "--name", "elasticsearch", DOCKER_IMAGE
    ]
    subprocess.run(docker_command, check=True)

    # Waiting for Elasticsearch to start
    print("Waiting for Elasticsearch to start...")
    for _ in range(20):
        if is_port_in_use(ES_PORT):
            print("Elasticsearch is running.")
            return
        time.sleep(5)

    print("Error: Elasticsearch did not start. Exiting.")
    sys.exit(1)

# Install Python dependencies
def install_python_dependencies():
    print("Installing required Python libraries...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "elasticsearch"], check=True)

# Connect to Elasticsearch
def connect_to_elasticsearch():
    print("Trying to connect to Elasticsearch server...")
    for attempt in range(20):
        try:
            print(f"Password retrieved: {ELASTIC_PASSWORD}")
            es = Elasticsearch(
                [ES_HOST],
                basic_auth=("elastic", ELASTIC_PASSWORD)
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
def create_custom_mapping(es, idx_name):
    if not os.path.exists(MAPPING_FILE):
        print(f"Error: {MAPPING_FILE} not found.")
        sys.exit(1)

    with open(MAPPING_FILE, 'r') as file:
        mapping = file.read()

    print(f"Creating custom mapping for Elasticsearch index '{idx_name}'...")
    if not es.indices.exists(index=idx_name):
        es.indices.create(index=idx_name, body=mapping)
        print("Index with custom mapping created.")
    else:
        print(f"Index '{idx_name}' already exists. Skipping creation.")

# Main setup process
def main():
    install_docker()
    run_elasticsearch()
    install_python_dependencies()
    es = connect_to_elasticsearch()
    create_custom_mapping(es, INDEX_NAME)
    create_custom_mapping(es, LINES_INDEX_NAME)
    #create_custom_mapping(es, "tmp_idx") # creating temporary index for searching lines
    print("Setup completed.")

if __name__ == "__main__":
    main()
