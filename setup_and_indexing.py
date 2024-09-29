import os
import subprocess
import time
import sys

# Configuration
ES_VERSION = "8.15.2"
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


# Pulling and running Elasticsearch using Docker (https://hub.docker.com/_/elasticsearch)
def run_elasticsearch():
    print(f"Pulling Elasticsearch image {DOCKER_IMAGE}...")
    subprocess.run(["docker", "pull", DOCKER_IMAGE])

    print("Running Elasticsearch...")
    subprocess.run([
        "docker", "run", "-d", "-p", f"{ES_PORT}:{ES_PORT}",
        "-e", "discovery.type=single-node", "--name", "elasticsearch", DOCKER_IMAGE
    ])

    # Waiting for Elasticsearch to start
    print("Waiting for Elasticsearch to start...")
    for _ in range(20):
        try:
            subprocess.check_output(["curl", "-s", ES_HOST])
            print("Elasticsearch is running.")
            return
        except subprocess.CalledProcessError:
            time.sleep(5)
            print("Waiting for Elasticsearch...")
    print("Error: Elasticsearch did not start. Exiting.")
    sys.exit(1)


# Creating custom mapping in Elasticsearch
def create_custom_mapping():
    if not os.path.exists(MAPPING_FILE):
        print(f"Error: {MAPPING_FILE} not found.")
        sys.exit(1)

    print(f"Creating custom mapping for Elasticsearch index '{INDEX_NAME}'...")

    # Creating index with custom mapping
    subprocess.run([
        "curl", "-X", "PUT", f"{ES_HOST}/{INDEX_NAME}",
        "-H", "Content-Type: application/json",
        "-d", f"@{MAPPING_FILE}"
    ])
    print("Custom mapping created.")


# Installing Python dependencies
def install_python_dependencies():
    print("Installing required Python libraries...")
    subprocess.run(["pip3", "install", "transformers", "elasticsearch"])


# Running the indexing script
def run_indexing_script():
    if os.path.exists("index_codebase.py"):
        print("Running the Python indexing script...")
        subprocess.run(["python3", "index_codebase.py"])
    else:
        print("Error: index_codebase.py script not found.")


# Main setup process
def main():
    install_docker()
    run_elasticsearch()
    create_custom_mapping()
    install_python_dependencies()
    run_indexing_script()
    print("Indexing completed.")


if __name__ == "__main__":
    main()
