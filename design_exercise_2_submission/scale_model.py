from email import message
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
    """
    Configuration class for a process.

    Attributes:
    -----------
    name: str
        Name of the process E.g P1, P2, etc
    host: str
        Ip address of the process to use when creating sockets.
    port: int
        Port that process uses to accept listen on for accepting new connections.
    out_ports: list of ports
        List of ports to which the current process will send.
    clock_rate: float
        Clock rate of the process
    rand_upper_bound: int
        Upper bound on the range of random numbers 
        from which we pick what event the process will run.
    """
    def __init__(self, name, host, listening_port, 
                 sending_ports = [], clock_rate = 1, rand_upper_bound = 9):
       self.name = name
       self.host = host
       self.port = listening_port
       self.out_ports = sending_ports
       self.clock_rate = clock_rate
       self.rand_upper_bound = rand_upper_bound

    def add_pid(self, pid): 
        self.pid = pid 
    

def consumer(client_socket):
    """
    Consumer thread function.
    This function is run by receiving thread and continually 
    appends new messages to the global state queue.
    Thread runs at REAL system clock rate

    Parameters
    ----------
    client_socket: socket.Socket
        Socket on which thread will be listening to.
    
    """
    print("consumer accepted connection" + str(client_socket)+"\n")
    while True:
        data = client_socket.recv(1024)
        dataVal = data.decode('ascii')
        print("msg received:", dataVal)
        lock.acquire()
        msg_queue.append(dataVal)
        lock.release()


 

def producer(config, port_idx):
    """
    Producer thread function.
    This function is run by the sending thread and continually,
    checks for operation code (set by MAIN thread) to determine whether 
    it needs to send a message or not.

    Parameters:
    config: Config instance
        Configuration details of the processor
    port_idx: int
        Index in the list of out_ports of the configuration that this sender thread 
        will always send to.
    
    """
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    out_port = config.out_ports[port_idx]
    try:
        sender_socket.connect((config.host, out_port))
        print("Client-side connection success to port val:" + str(out_port) + "\n")

        while True:
            lock.acquire()
            clock_read_flag[port_idx] = True
            if out_port in code:
                # send to one of the other machines a message that is the 
                # local logical clock time, update it’s own logical clock, 
                # and update the log with the send, the system time, 
                # and the logical clock time
                
                sender_socket.send(str(logical_clock).encode('ascii'))
                # Update log with the send info
                logger.info(f"event: SENT to {out_port}, sys_clock: {clock}, logical_clock: {logical_clock}, code: {action}, queue_length: {len(msg_queue)}")
            lock.release()
            time.sleep(clock_rate)
            
    except Exception as e:
        print("Error connecting producer: %s" % e)
 

def init_machine(config):
    """
    Thread function to accept new connections and create sockets for them.

    Parameters
    ----------
    config: Config instance
        Configuration details of the processor

    """
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

def machine(config, log_folder):
    """
    MAIN thread function that simulates the a machine running
    at a clock rate.

    Parameters
    ----------
    config: Config instance
        Configuration details of the processor.
    log_folder: str
        Name of the folder where logs files are to be stored.

    Globals
    -------

    code: list of ints
    action: int
    clock_rate: float
    msg_queue: list of ints
    logger
    logical_clock
    clock
    clock_read_flag

    """

    config.add_pid(os.getpid())
    global code
    code = []

    global action 
    action = -1 
    
    global clock_rate
    clock_rate = config.clock_rate

    global logger
    logger = setup_logger(f'{config.name}_pid_{config.pid}', f'./{log_folder}/{config.name}_pid_{config.pid}.log')
    logger.info(f"Hello from process {config.name} with pid {config.pid} at rate {clock_rate}")

    global msg_queue
    msg_queue = []

    global lock
    lock = threading.Lock()

    global logical_clock
    logical_clock = 0

    global clock
    clock = 0

    global clock_read_flag
    clock_read_flag = [False for _ in config.out_ports]


    init_thread = Thread(target=init_machine, args=(config,))
    init_thread.start()
    # Add delay to initialize the server-side logic on all processes
    time.sleep(5)

    thread_list = []
    for port_idx, _ in enumerate(config.out_ports):
        # extensible to multiple producers
        prod_thread = Thread(target=producer, args=(config, port_idx))
        thread_list.append(prod_thread)
    for thread in thread_list:
        thread.start()

    while True:
        time.sleep(clock_rate)

        # Handle Read-after-write error
        while sum(clock_read_flag) != len(clock_read_flag):
            continue
        lock.acquire()

        # UNIT TEST: Assert that all sender threads have sent the message before 
        # simulated clock in MAIN thread is increased.
        for flag in clock_read_flag:
            assert flag == True 

        logical_clock += 1
        clock += 1
        clock_read_flag = [False for _ in config.out_ports]

        # If there is a message in the queue
        if msg_queue:
            msg = msg_queue.pop(0)
            logger.info(f"event: RECEIVE MESSAGE, sys_clock: {clock}, logical_clock: {logical_clock}, code: {-1}, queue_length: {len(msg_queue)}, msg: {msg}")
            logical_clock = max(logical_clock, int(msg))
            code = [] 
        else: 
            # UNIT TEST: Assert Invariant that sending only happens when queue is empty
            assert len(msg_queue) == 0 
            action = random.randint(0,config.rand_upper_bound)
            if action in list(range(len(config.out_ports))):
                """ Send to ONE of the other machines a message that is:
                    - the local logical clock time, 
                    - update it's own logical clock, 
                    - and update the log with the send, 
                    - the system time, and 
                    - the logical clock time"""
                code = [config.out_ports[action]]
            elif action == len(config.out_ports):
                code = config.out_ports
            else:
                """Treat the cycle as an internal event: 
                - update the local logical clock, 
                - log the internal event, the system time, and the logical clock value."""
                code = []
                logger.info(f"event: INTERNAL EVENT, sys_clock: {clock}, logical_clock: {logical_clock}, code: {action}, queue_length: {len(msg_queue)}")
            
            # UNIT TEST: Assert invariant that action is within the defined options
            assert action in list(range(-1, config.rand_upper_bound+1))
        lock.release()
   

localHost= "127.0.0.1"

def run_experiment(random_ = True, clock_rates = [1, 1, 1], rand_upper = 9): 
    port1 = 2056
    port2 = 3056
    port3 = 4056
 
    if random_: 
        clock_rates = [1 / random.randint(1, 6), 1 / random.randint(1, 6),1 / random.randint(1, 6)]
    # random.seed(262)
    log_folder =f"/experiment_rates_{'-'.join(['%.2f' % elem for elem in clock_rates])}_rand_{rand_upper}"
    os.makedirs(f"{os.getcwd()}{log_folder}")
    print('P1 clock rate: ', clock_rates[0])
    config1 = Config('P1', localHost, port1, [port2, port3], clock_rates[0], rand_upper)
    p1 = Process(target=machine, args=(config1, log_folder,))

    print('P2 clock rate: ', clock_rates[1])
    config2 = Config('P2', localHost, port2, [port1, port3], clock_rates[1], rand_upper)
    p2 = Process(target=machine, args=(config2,log_folder, ))
    
    print('P3 clock rate: ', clock_rates[2])
    config3 = Config('P3', localHost, port3, [port1, port2], clock_rates[2], rand_upper)
    p3 = Process(target=machine, args=(config3,log_folder, ))
    
    p1.start()
    p2.start()
    p3.start()
    
    time.sleep(200)

    p1.kill()
    p2.kill()
    p3.kill()


if __name__ == '__main__':
    delete_log_files(os.getcwd())
    run_experiment(random_=False, clock_rates = [1/6, 1/6, 1])
    # rates = [[1, 1, 1], [1/6, 1/6, 1], [1, 1, 1/6], [1/6, 1/4, 1/2], [1/3, 1/2, 1/4], [1/10, 1, 1], [1/10, 1/10, 1]]
    # for rate_exp in rates: 
    #     run_experiment(random_=False, clock_rates = rate_exp)

    # for rate_exp in rates[:4]:
    #     for rand_upper in [3, 5, 7]: 
    #         run_experiment(random_=False, clock_rates = rate_exp, rand_upper=rand_upper)

    