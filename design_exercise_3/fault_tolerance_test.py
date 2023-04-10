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


    db1 = pickledb.load(config.CONFIG["rep_server1"]["db_file"], True)
    db2 = pickledb.load(config.CONFIG["rep_server2"]["db_file"], True)
    db3 = pickledb.load(config.CONFIG["rep_server3"]["db_file"], True)


    # assert new user signup is correctly reflected in all servers log and db
    assert (pend_log1.get('last_entry') == pend_log2.get('last_entry'))
    assert (pend_log1.get('last_entry') == pend_log3.get('last_entry'))
    assert (db1.get('userA') == db2.get('userA'))
    assert (db1.get('userA') == db3.get('userA'))

    client2.command = 'sign_up'
    client2.user = chat_app_pb2.User(username = 'userB')
    client2.run_command() 

    client3.command = 'sign_up'
    client3.user = chat_app_pb2.User(username = 'userC')
    client3.run_command() 

    # assert new user signup is correctly reflected in all servers log and db
    assert (pend_log1.get('last_entry') == pend_log2.get('last_entry'))
    assert (pend_log1.get('last_entry') == pend_log3.get('last_entry'))
    assert (db1.get('userA') == db2.get('userA'))
    assert (db1.get('userA') == db3.get('userA'))

    # check replication for other commands as well (delete user, send_message, receive_message)
    client1.command = 'send_message'
    client1.destinataries = [chat_app_pb2.User(username='userB'), chat_app_pb2.User(username='userC')]
    client1.message = 'hey everyone'
    client1.run_command()

    # check that pending messages for userB is the same in all 3 servers 
    assert (db1.get('userB') == db2.get('userB'))
    assert (db1.get('userB') == db3.get('userB'))

    # check that pending message gets removed on all databases 
    client2.command = 'receive_message'
    client2.run_command() 

    assert (db1.get('userB') == db2.get('userB'))
    assert (db1.get('userB') == db3.get('userB'))

    client3.command = 'receive_message'
    client3.run_command() 

    for i, process in enumerate(processes):
        if i == 2: 
            # crash the first 2 servers 
            break 
        print(f"Killing server {i + 1}")
        process.kill()
        client1.command = 'listall'
        client1.run_command()
        time.sleep(10)
    processes[2].kill()
    

if __name__ == '__main__': 
    main()
