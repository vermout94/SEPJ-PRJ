### Software Engineering Project - Group 13
ReadMe   
Version: 1.0, Date: 2025-01-12

# SmartSearch - A tool for smart search in a codebase

## 1. Setup

### Installing Python

Be aware that this search tool relies on the usage of python script files.
Therefore, make sure that Python is installed on those machines where the tool should be deployed.

For the setup and usage of Python the online documentation is referenced:   
https://docs.python.org/3/using/index.html

A widely used open source distribution platform for Python is Anaconda which includes the installation of Python itself:   
https://www.anaconda.com/download

### Installing Docker

Download Docker Desktop: 
https://www.docker.com/get-started/  
choose the version suitable for your OS (Windows, Linux or Mac)

### Installing Elasticsearch Server with Docker
Guide in online documentation for manual installation:
https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html

This starts up an Elasticsearch server as a single-node cluster running locally in a Docker container.

NOTE: The start-up and configuration of the docker container can also be done automatically by the provided setup script.

### Running Elasticsearch Setup Script

Open the project folder in the IDE of your choice (e.g. PyCharm) or simply open a terminal for execution of commands and change to the directory of the project's files.

Run the script file "setup.py" in the project source folder:

```
python setup.py
```

This script will check if Docker is already installed. Windows users have to install Docker Desktop manually.
Next, the script is checking if the expected port of elasticsearch (9200 by default) is already in use.
In such case it is assumed that the server is currently running.
If not, the docker image of Elasticserach is downloaded and a new container is started up.
Port and password are configured and a connection to the Elasticsearch server is established in order to create the required indices with custom mapping.


## 2. Index Codebase

The step of indexing the codebase has to be done before any search can be performed.
Only indexed files are considered in processing a search query! 

Run the script file "index_codebase.py" in the project source folder:

```
python index_codebase.py C:\Users\...\SEPJ-PRJ\test_files
```

The filepath of the codebase directory has to be provided as argument!
The execution of this command could also be integrated into the build process or into a CI/CD pipeline.
If any changes have been done (new files added, existing files modified or removed) the indexing or updating of the indices should be triggered by running this script file.

The procedure within the script uses a pre-trained llm (large language model) for tokenization and transformation of the code content into vectors to be indexed in the Elasticsearch database.
There is one index created having a document for each file of the codebase and another index for having a document for each line of each file.


## 3. Performing a Search Query

There is no graphical user interface provided - only a command line interface is available.

Execute the script file "search_codebase_cli.py" in the project source folder:

```
python search_codebase_cli.py
```
This will start the search tool in the command line.
There you can choose the desired type of search and enter a term or any question to which you want to find the corresponding place in code.
The search tool tries to determine the files of the codebase and the related lines in code which are most relevant in respect to your input.
The result list is ordered by ranking of the obtained score.
This scoring is given by how similar the input is compared to the found code. 
Therefore, the search input is also transformed into a vector like it is done while indexing by using the same llm.
This procedure is called "vector search" and its implementation in this tool is based on the k-nearest-neighbours algorithm.
