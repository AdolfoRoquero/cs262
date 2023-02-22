from utils import * 
from client import *
import random 
import string 
from protocol import *
import time
import os


def run(): 
    host = '192.168.0.114'
    port = '50051'
    setup_client = Client(host=host, 
                                  port=port)
    setup_client.setup()
    username = 't'

    # signup message size 
    result = setup_client.sign_up(username)
    print(f'CLIENT signup message: {result}')
    

    # login message size 
    result = setup_client.login(username)
    print(f'CLIENT login message: {result}')

    # listall message size 
    username_filter = '*'
    result = setup_client.listall(username_filter)
    print(f'CLIENT listall {username_filter}: {result}')

    # listall message size with filter
    letters = string.ascii_lowercase
    random_filter = ''.join(random.choice(letters) for i in range(8))
    username_filter = '*' + random_filter
    result = setup_client.listall(username_filter)
    print(f'CLIENT listall {username_filter}: {result}')

    # send message message size 
    message = ""
    destinatary = "a"
    result = setup_client.send_message(destinatary, message)
    print(f'CLIENT send message "{message}": {result}')

    # send message message size 
    message = "Hello"
    destinatary = "a"
    result = setup_client.send_message(destinatary, message)
    print(f'CLIENT send message "{message}": {result}')

    # receive message size 
    result = setup_client.receive_message()
    print(f'CLIENT receive message: {result}')
    
    # delete_user message size 
    result = setup_client.del_user()
    print(f'CLIENT delete user: {result}')

    

if __name__ == "__main__":
    run()  

