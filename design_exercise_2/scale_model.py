from multiprocessing import Process
import os
import socket
from _thread import *
import threading
import time
from threading import Thread
import random
 

class Config: 
    def __init__(self, host, listening_port, sending_ports = [], clock_rate = 1):
       self.host = host
       self.port = listening_port
       self.out_ports = sending_ports
       self.clock_rate = clock_rate

    def add_pid(self, pid): 
        self.pid = pid 

def consumer(conn):
    print("consumer accepted connection" + str(conn)+"\n")
    msg_queue = []
    sleepVal = clock_rate
    while True:
        time.sleep(sleepVal)
        data = conn.recv(1024)
        print("msg received\n")
        dataVal = data.decode('ascii')
        print("msg received:", dataVal)
        msg_queue.append(dataVal)
 

def producer(config):
    portVal = config.out_ports[0]
    port = int(portVal)
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sleepVal = clock_rate
    #sema acquire
    try:
        s.connect((config.host,port))
        print("Client-side connection success to port val:" + str(portVal) + "\n")
    
        while True:
            codeVal = str(code)
            time.sleep(sleepVal)
            s.send(codeVal.encode('ascii'))
            print("msg sent", codeVal, "to port ", port, "from P listening at ", config.port)
            
    except socket.error as e:
        print ("Error connecting producer: %s" % e)
 

def init_machine(config):
    HOST = str(config.host)
    PORT = int(config.port)
    print("starting server| port val:", PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        start_new_thread(consumer, (conn,))
    

def machine(config):
    config.add_pid(os.getpid())
    global code
    global clock_rate 
    clock_rate = config.clock_rate
    init_thread = Thread(target=init_machine, args=(config,))
    init_thread.start()
    #add delay to initialize the server-side logic on all processes
    time.sleep(5)
    # extensible to multiple producers
    prod_thread = Thread(target=producer, args=(config,))
    prod_thread.start()
    while True:
        code = random.randint(1,3)

localHost= "127.0.0.1"
 
if __name__ == '__main__':
    port1 = 2056
    port2 = 3056
    port3 = 4056
 
    random.seed(262)

    clock_rate = 1 / random.randint(1, 6)
    print('P1 clock rate: ', clock_rate)
    config1 = Config(localHost, port1, [port2, port3], clock_rate)
    p1 = Process(target=machine, args=(config1,))

    clock_rate = 1 / random.randint(1, 6)
    print('P2 clock rate: ', clock_rate)
    config2 = Config(localHost, port2, [port1, port3], clock_rate)
    p2 = Process(target=machine, args=(config2,))
    
    clock_rate = 1 / random.randint(1, 6)
    print('P3 clock rate: ', clock_rate)
    config3 = Config(localHost, port3, [port1, port2], clock_rate)
    p3 = Process(target=machine, args=(config3,))
    
    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
