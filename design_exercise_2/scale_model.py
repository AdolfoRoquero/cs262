from multiprocessing import Process
import os
import socket
from _thread import *
import threading
import time
from threading import Thread
import random
import logging
from datetime import datetime 

def delete_log_files(dir=os.getcwd()):
    for path in os.listdir(dir):
        if path.endswith('.log'):
            os.remove(path)	

    

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

class Config: 
    def __init__(self, name, host, listening_port, 
                 sending_ports = [], clock_rate = 1):
       self.name = name
       self.host = host
       self.port = listening_port
       self.out_ports = sending_ports
       self.clock_rate = clock_rate

    def add_pid(self, pid): 
        self.pid = pid 

def consumer(client_socket):
    print("consumer accepted connection" + str(client_socket)+"\n")
    sleepVal = clock_rate
    while True:
        data = client_socket.recv(1024)
        dataVal = data.decode('ascii')
        print("msg received:", dataVal)
        lock.acquire()
        msg_queue.append(dataVal)
        lock.release()


 

def producer(config, out_port):
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sender_socket.connect((config.host, out_port))
        print("Client-side connection success to port val:" + str(out_port) + "\n")

        while True:
            lock.acquire()
            if out_port in code:
                # send to one of the other machines a message that is the 
                # local logical clock time, update it’s own logical clock, 
                # and update the log with the send, the system time, 
                # and the logical clock time
                
                sender_socket.send(str(logical_clock).encode('ascii'))
                system_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                # Update log with the send info
                logger.info(f"SENT from {config.host} to {out_port} at {system_time}, sys_clock:{clock} logical_clock: {logical_clock}, code: {code}")
            lock.release()
            time.sleep(clock_rate)
            
    except Exception as e:
        print("Error connecting producer: %s" % e)
 

def init_machine(config):
    print("starting server| port val:", int(config.port))
    try: 
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((str(config.host), int(config.port)))
        server_socket.listen()
        while True:
            client_socket, address = server_socket.accept()
            start_new_thread(consumer, (client_socket,))
    
    except Exception as e:
        print("Error accepting client sockets: %s" % e)

def machine(config):
    config.add_pid(os.getpid())
    global code
    code = []
    
    global clock_rate
    clock_rate = config.clock_rate

    global logger
    logger = setup_logger(f'{config.name}_pid_{config.pid}', f'{config.name}_pid_{config.pid}.log')
    logger.info(f"Hello from process {config.name} with pid {config.pid} at rate {clock_rate}")

    global msg_queue
    msg_queue = []

    global lock
    lock = threading.Lock()

    global logical_clock
    logical_clock = 0

    global clock
    clock = 0


    init_thread = Thread(target=init_machine, args=(config,))
    init_thread.start()
    #add delay to initialize the server-side logic on all processes
    time.sleep(5)

    thread_list = []
    for out_port in config.out_ports:
        # extensible to multiple producers
        prod_thread = Thread(target=producer, args=(config, out_port))
        thread_list.append(prod_thread)
    for thread in thread_list:
        thread.start()

    while True:
        time.sleep(clock_rate)

        lock.acquire()
        logical_clock += 1
        clock += 1

        # If there is a message in the queue
        if msg_queue:
            msg = msg_queue.pop(0)
            system_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            logger.info(f"RECEIVE MESSAGE at {system_time}, sys_clock: {clock}, logical_clock: {logical_clock}, msg: {msg}, queue_length: {len(msg_queue)}")
            logical_clock = max(logical_clock, int(msg))
        else: 
            rand_action = random.randint(0,9)
            if rand_action in list(range(len(config.out_ports))):
                """ Send to ONE of the other machines a message that is:
                    - the local logical clock time, 
                    - update it's own logical clock, 
                    - and update the log with the send, 
                    - the system time, and 
                    - the logical clock time"""
                code = [config.out_ports[rand_action]]
            elif rand_action == len(config.out_ports):
                code = config.out_ports
            else:
                """Treat the cycle as an internal event: 
                - update the local logical clock, 
                - log the internal event, the system time, and the logical clock value."""
                code = []
                system_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                logger.info(f"INTERNAL EVENT at {system_time}, sys_clock: {clock}, logical_clock: {logical_clock}")
        
        lock.release()
   

localHost= "127.0.0.1"
 
if __name__ == '__main__':
    delete_log_files(os.getcwd())
    port1 = 2056
    port2 = 3056
    port3 = 4056
 
    # random.seed(262)

    clock_rate = 1 / random.randint(1, 6)
    clock_rate = 1
    print('P1 clock rate: ', clock_rate)
    config1 = Config('P1', localHost, port1, [port2, port3], clock_rate)
    p1 = Process(target=machine, args=(config1,))

    clock_rate = 1 / random.randint(1, 6)
    clock_rate = 1/3

    print('P2 clock rate: ', clock_rate)
    config2 = Config('P2', localHost, port2, [port1, port3], clock_rate)
    p2 = Process(target=machine, args=(config2,))
    
    clock_rate = 1 / random.randint(1, 6)
    clock_rate = 1/6
    print('P3 clock rate: ', clock_rate)
    config3 = Config('P3', localHost, port3, [port1, port2], clock_rate)
    p3 = Process(target=machine, args=(config3,))
    
    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
