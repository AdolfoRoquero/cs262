#!/bin/bash

# Kill previous run
pkill -f node.py


# Run servers
ttab -w 'source env.sh; poetry run python node.py'
ttab -w 'source env.sh; poetry run python node.py --port 50070'
ttab -w 'source env.sh; poetry run python node.py --port 50074'
ttab -w 'source env.sh; poetry run python node.py --port 50100'
