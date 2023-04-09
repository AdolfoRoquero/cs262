import os

CONFIG = {
        "rep_server1" : {
            "host": os.environ["REP_SERVER_HOST_1"],
            "port": os.environ["REP_SERVER_PORT_1"],
            "pend_log_file": os.environ["REP_SERVER_PEND_1"],
            "db_file": os.environ["REP_SERVER_DB_FILE_1"],
        },
        "rep_server2" : {
            "host": os.environ["REP_SERVER_HOST_2"],
            "port": os.environ["REP_SERVER_PORT_2"],
            "pend_log_file": os.environ["REP_SERVER_PEND_2"],
            "db_file": os.environ["REP_SERVER_DB_FILE_2"],
        },
        "rep_server3" : {
            "host": os.environ["REP_SERVER_HOST_3"],
            "port": os.environ["REP_SERVER_PORT_3"],
            "pend_log_file": os.environ["REP_SERVER_PEND_3"],
            "db_file": os.environ["REP_SERVER_DB_FILE_3"],
        }
    }

STARTING_PRIMARY_SERVER = 'rep_server1'
