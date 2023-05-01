#!/bin/bash

# Kill previous run
pkill -f node.py


# Run servers
ttab -w 'source env.sh; poetry run python node.py -s 1'
ttab -w 'source env.sh; poetry run python node.py --server 2 --port 50070'
ttab -w 'source env.sh; poetry run python node.py --server 3 --port 50074'
