import os
import subprocess
import time
import sys
import socket
import platform
import docker
from elasticsearch import Elasticsearch

# Configuration
ES_VERSION = "8.15.3"
ES_PORT = 9200
ES_HOST = f"https://localhost:{ES_PORT}"
INDEX_NAME = "codebase_index"
LINES_INDEX_NAME = "codebase_lines_index"
DOCKER_IMAGE = f"docker.elastic.co/elasticsearch/elasticsearch:{ES_VERSION}"
CERTIFICATE_PATH = f"elasticsearch:/usr/share/elasticsearch/config/certs/http_ca.crt"
MAPPING_FILE = "custom_mapping.json"
ELASTIC_USER = os.getenv('ES_USERNAME', 'elastic')
ELASTIC_PASSWORD = os.getenv('ES_PASSWORD', 'password')

# Check platform
IS_WINDOWS = platform.system().lower() == "windows"

def check_docker():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception as e:
        return False

def start_docker_desktop():
    try:
        # Path to Docker Desktop executable
        docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        # Start Docker Desktop
        subprocess.run([docker_path], check=True)
        print("Docker Desktop started successfully.")
    except Exception as e:
        print(f"An error occurred when trying to start Docker Desktop: {e}")

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
        docker_is_started = False

        for _ in range(20):
            if check_docker():
                print("Docker is running.")
                break
            else:
                print("Docker is not running.")
                if not docker_is_started:
                    if IS_WINDOWS:
                        start_docker_desktop()
                    else:
                        subprocess.run(["open", "-a", "docker"])
                    docker_is_started = True
            time.sleep(3)

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
        "docker", "run", "-d", "--name", "elasticsearch",
        "-p", f"{ES_PORT}:{ES_PORT}",
        "-it", "-m", "1GB",
        "-e", f"ELASTIC_PASSWORD={ELASTIC_PASSWORD}",
        DOCKER_IMAGE
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

def get_elasticsearch_certificate():
    print("Retrieving elasticsearch server certificate...")
    for attempt in range(30):
        try:
            time.sleep(3)
            docker_command = ["docker", "cp", CERTIFICATE_PATH, f"./"]
            subprocess.run(docker_command, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}: failed, retrying...")
        time.sleep(3)

# Connect to Elasticsearch
def connect_to_elasticsearch():
    print("Trying to connect to Elasticsearch server...")

    for attempt in range(40):
        try:
            es = Elasticsearch(
                [ES_HOST],
                basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
                ca_certs=r"./http_ca.crt",
                verify_certs=True
            )
            if es.ping():
                print("Connected to Elasticsearch")
                return es
            else:
                print(f"Connecting ...")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Connection failed due to {e}, retrying...")
        time.sleep(15)

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
    get_elasticsearch_certificate()
    es = connect_to_elasticsearch()
    create_custom_mapping(es, INDEX_NAME)
    create_custom_mapping(es, LINES_INDEX_NAME)

    print("Setup completed.")

if __name__ == "__main__":
    main()
