# 2-Fault Tolerant and persistent Chat Application - CS262 Design Exercise 3 - Spring 2023

## Description
This folder contains an extension of the grpc implementation of the Chat Application found in https://github.com/AdolfoRoquero/cs262/tree/main/design_exercise_1. 

## Setup 

### Connection configuration
- Go to your network settings on your PC and find your IP address
- Open `env.sh` file and edit `REP_SERVER_HOST_1`, `REP_SERVER_HOST_2`, `REP_SERVER_HOST_3` environment variable with your IP. To run the servers across different machines, simply set these values to each of the distinct IP addresses. 
- Inside your environment, run `source env.sh` or install individually export the environment variables (On Windows).

### Dependencies 

- Python version Python 3.9+
- grpcio==1.51.3
- grpcio-tools==1.51.3
- protobuf==4.22.0
- pickledb 
All required packages can be installed with Pip from the provide requirements.txt file via the pip install -r requirements.txt command. For troubleshooting the installation of GRPC packages, go to https://grpc.io/docs/languages/python/quickstart/

## Running the code: Step-by-step guide
---------------------------------------
1. Create virtual environement for the project:
    - Linux/Mac: `python3.9 -m venv CS262_venv` then `source CS262_venv/bin/activate`
2. Add environment variables:
    - Linux/Mac: `source env.sh`
3. Install dependencies:
    - Linux/Mac/Windows: `pip install -r requirements.txt`
4. Run Server on a new terminal (with venv activated):
    - To run all the server instances as different processes in the same machine: 
        - `python server.py --server 0`
    - To run a single server instance, enter in separate terminals (either in the same or different machines): 
        - `python server.py --server 1` to initialize the first server 
        - `python server.py --server 2` to initialize the second server 
        - `python server.py --server 3` to initialize the third server 
        - the `--server` flag can also be replaced with `-s` 
    - To reboot a server (i.e. after a whole system crash to restart a server with the key value store and log it had before it crashed) add the `--reboot` or `-r` flag. 
        - `python server.py --server 1 --reboot` to reboot server 1 
    - To manually set one of the servers as the primary add the `--primary` or `-p` flag. Defaults with server 1 as the primary: 
        - `python server.py --server 2 --primary --reboot` to reboot server 2 as the primary server 
5. Run Client on a new terminal (a new terminal per new client):
    - `python client.py`
6. Interact with the prompts in the Client Terminal

