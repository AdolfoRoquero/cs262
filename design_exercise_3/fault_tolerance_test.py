import unittest 
import string 
import random 
import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 
import client 
import config
from server import server, ChatAppServicer
import threading
from multiprocessing import Process
import time
import pickledb 

def main(): 
    processes = [] 
    for rep_server in config.CONFIG:
        p = Process(target=server, args=(rep_server, 'rep_server1', config.CONFIG, False))
        processes.append(p)
    for process in processes:
        process.start()
    
    time.sleep(5)

    client1 = client.Client(config.CONFIG, config.STARTING_PRIMARY_SERVER)
    client2 = client.Client(config.CONFIG, config.STARTING_PRIMARY_SERVER)
    client3 = client.Client(config.CONFIG, config.STARTING_PRIMARY_SERVER)

    client1.command = 'sign_up'
    client1.user = chat_app_pb2.User(username = 'userA')
    client1.run_command() 

    time.sleep(5)
    pend_log1 = pickledb.load(config.CONFIG["rep_server1"]["pend_log_file"], True)
    pend_log2 = pickledb.load(config.CONFIG["rep_server2"]["pend_log_file"], True)
    pend_log3 = pickledb.load(config.CONFIG["rep_server3"]["pend_log_file"], True)
    assert (pend_log1.get('last_entry') == pend_log2.get('last_entry'))
    time.sleep(5)
    for process in processes:
            process.kill()


if __name__ == '__main__': 
    main()
