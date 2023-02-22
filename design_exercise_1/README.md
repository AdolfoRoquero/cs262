# Chat Application - CS262 Design Exercise 1 - Spring 2023

## Description
This folder contains two implementations of the Chat Application. 
- Socket Implementation under `socket/` folder
- GRCP Implementation under `grpc/` folder


## Setup
-----------

### Connection configuration
- Go to your network settings on your PC and find your IP address
- Open `env.sh` file and edit `CHAT_APP_SERVER_HOST` environment variable with your IP
- Inside your environment, run `source env.sh` or install individually export the environment variables (On Windows).

### Dependencies
- Python version Python 3.9+
- `grpcio==1.51.3`
- `grpcio-tools==1.51.3`
- `protobuf==4.22.0`

All required packages can be installed with Pip from the provide `requirements.txt` file via the `pip install -r requirements.txt` command.
For troubleshooting the installation of GRPC packages, go to https://grpc.io/docs/languages/python/quickstart/

## Running the code: Step-by-step guide
---------------------------------------
1. Create virtual environement for the project:
    - Linux/Mac: `python3.9 -m venv CS262_venv` then `source CS262_venv/bin/activate`
2. Add environment variables:
    - Linux/Mac: `source env.sh`
3. Install dependencies:
    - Linux/Mac/Windows: `pip install -r requirements.txt`
4. Run Server on a new terminal (with venv activated):
    - `python <socket_or_grpc>/server.py`
5. Run Client on a new terminal (a new terminal per new client):
    - `python <socket_or_grpc>/client.py`
6. Interact with the prompts in the Client Terminal


## Testing the code: Step-by-step guide
- Socket:
    1. Run `python socket/server.py`
    2. Run `python socket/test.py`
- GRPC:
    1. Run `python grpc/server.py`
    2. Run `python grpc/test.py`





