#!/bin/bash

#
# Quip2P2lash - CS262 Final Project - RUN 3 NODES
# This script runs 3 P2P nodes to play the game 
# (you must have run setup.sh BEFORE)
#

# Kill previous run
pkill -f node.py

# Run servers
ttab -w 'source CS262_venv/bin/activate; python node.py --port 50100'
ttab -w 'source CS262_venv/bin/activate; python node.py --port 50200'
ttab -w 'source CS262_venv/bin/activate; python node.py --port 50300'
