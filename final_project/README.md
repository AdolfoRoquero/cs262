# Quip2P2lash - CS262 Final Project - Spring 2023

## Description
For our final project, we implemented Quip2P2lash, the peer-to-peer version of the famous Jackbox.TV game Quiplash

This folder contains two implementations of the Quip2P2lash. 
- TerminalBased Implementation
- Tkinter-UI Implementation under `tkinter/` folder (WORK IN PROGRESS)

## Setup
-----------

### Dependencies
- Python version: Python 3.11
- `grpcio-tools==1.54.0`
- `grpcio==1.54.0`
- `inputimeout==1.0.4`
- `numpy==1.24.3`
- `pickledb==0.9.2`
- `pillow==9.5.0`
- `protobuf==4.22.3`
- `setuptools==67.7.2`

All required packages can be installed with Pip from the provided `requirements.txt` file via the `pip install -r requirements.txt` command.
For troubleshooting the installation of GRPC packages, go to https://grpc.io/docs/languages/python/quickstart/

## Running the code:
--------------------

###  Step-by-step guide
1. Create virtual environement for the project:
    - Linux/Mac: `python3.11 -m venv CS262_venv` then `source CS262_venv/bin/activate`
2. Install dependencies:
    - Linux/Mac/Windows: `pip install -r requirements.txt`
3. Run Node on terminal (with venv activated):
    - `python terminal/node.py`
    - Optionally, you can provide a specific port of your machine to run the node on if you desire with the `--port` flag.
    - This will run ONE node of the peer to peer network. 
      If you want to run multiple nodes, activate 
      the venv on another terminal and rerun `python node.py`

### With our helper bash scripts (Only if you have `ttab` installed)
1. Give execution permissions to `setup.sh`:
    - Run `chmod +x setup.sh`
1. Set up virtual environment and requirements:
    - Run `./setup.sh`
3. Give execution permissions to `run.sh`:
    - Run `chmod +x run.sh`
4. Run 3 Node set up:
    - Run `./run.sh`
This will open several terminals and run a P2P node in them. (see `run.sh`)
5. Clean up generated log files
    - Run `./clean.sh`

## Testing the code
- Test:
    1. Run `python unit_test.py`





