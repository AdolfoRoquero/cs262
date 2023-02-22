import socket
import sys
import errno
from protocol import *
from utils import * 
import traceback
from functools import wraps
import os



class Client():
    def __init__(self, host, 
                       port):
        self.host = host
        self.port = int(port)
        
        self.is_logged_in = False

    def setup(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        # print(f"Client connected to host {self.host}:{self.port}")
        self.client_socket.setblocking(False)
    
    def login(self, username):
        metadata_hdr = create_metadata_header(CL_LOGIN, username)
        sent = self.client_socket.send(metadata_hdr)
        self.username = username
        self.is_logged_in = True
        return sent
    
    def sign_up(self, username):
        metadata_hdr = create_metadata_header(CL_SIGNUP, username)
        sent = self.client_socket.send(metadata_hdr)
        self.username = username
        self.is_logged_in = True
        return sent
    
    def listall(self, username_filter):
        if not self.is_logged_in:
            raise Exception("ListAll requires the client to be logged in")

        metadata_hdr = create_metadata_header(CL_LISTALL, self.username)
        username_filter_enc = encode_message_segment(username_filter, MSG_HDR_SZ)
        sent = self.client_socket.send(metadata_hdr + username_filter_enc)        
        return sent
    
    def del_user(self):
        if not self.is_logged_in:
            raise Exception("Deleting a user requires the client to be logged in")
        metadata_hdr = create_metadata_header(CL_DEL_USER, self.username)
        sent = self.client_socket.send(metadata_hdr)
        return sent

    def send_message(self, dest, msg):
        if not self.is_logged_in:
            raise Exception("ListAll requires the client to be logged in")
        metadata_hdr = create_metadata_header(CL_SEND_MSG, self.username)
        # Encode destinatary
        dest_enc = encode_message_segment(dest, DESTINATARIES_HDR_SZ)
        
        # Encode message
        message_enc = encode_message_segment(msg, MSG_HDR_SZ)

        sent = self.client_socket.send(metadata_hdr + dest_enc + message_enc)
        return sent

    def close(self):
        if not self.is_logged_in:
            raise Exception("ListAll requires the client to be logged in")
        self.client_socket.close()

    def receive_message(self):
        if not self.is_logged_in:
            raise Exception("ListAll requires the client to be logged in")

        # Read metadata 
        metadata = read_metadata_header(self.client_socket)

        if not metadata: 
            return False 

        message = {'metadata': metadata}

        if message['metadata']['message_type'] == SRV_LISTALL: 
            # Read destinataries 
            message_content_str = unpack_message_segment(self.client_socket, DESTINATARIES_HDR_SZ)
            message['message_content'] = message_content_str.split(',')
            return message

        elif message['metadata']['message_type'] in [SRV_DEL_USER, SRV_MSG_FAILURE, SRV_SIGNUP, SRV_LOGIN]:
            message_content = unpack_message_segment(self.client_socket, MSG_HDR_SZ)
            if not message_content: 
                return False 
            message['message_content'] = message_content
            return message

        elif message['metadata']['message_type'] == SRV_FORWARD_MSG: 
            sender_username =  unpack_message_segment(self.client_socket, USERNAME_HDR_SZ)
            if not sender_username: 
                return False
            
            sender_timestamp = unpack_message_segment(self.client_socket, TIMESTAMP_SZ)

            if not sender_timestamp: 
                return False

            message_hdr = self.client_socket.recv(MSG_HDR_SZ)
            
            # Connection Error
            if not (len(message_hdr)):
                return False

            message_length = int(message_hdr.decode('utf-8').strip())
            message_content = self.client_socket.recv(message_length).decode('utf-8').strip()
            
            message['sender_timestamp'] = sender_timestamp
            message['sender_username'] = sender_username
            message['message_content'] = message_content
            return message


if __name__ == '__main__':
    client = Client(host=os.environ['CHAT_APP_SERVER_HOST'],
                    port=os.environ['CHAT_APP_SERVER_PORT'])
    client.setup()

    waiting_for_response = False

    while True:
        new_or_existing = input("New or existing user (N or E): ").strip().lower()
        if new_or_existing == 'e':
            client_msg_type = CL_LOGIN  
            break
        elif new_or_existing == 'n':
            client_msg_type = CL_SIGNUP
            break

    username = input("Enter username: ").strip().lower()

    if client_msg_type == CL_SIGNUP:
        sent = client.sign_up(username) 
        waiting_for_response = True 
    elif client_msg_type == CL_LOGIN:
        sent = client.login(username) 
        waiting_for_response = True 
    
    command = ''
    while True:
        # wait for message 
        if not waiting_for_response:
            print(f"Commands: 'listall <wildcard>', 'delete_user', 'send_message' OR <enter> to refresh")
            command = input(f"{username}> ").strip()

        if command.startswith("listall"):

            username_filter = command.replace('listall', '').strip()
            sent = client.listall(username_filter) 
            waiting_for_response = True
            command = ''
        
        elif command == "delete_user":
            sent = client.del_user()
            waiting_for_response = True
            command = ''

        elif command == "send_message":
            dest = input(f"{username}> Destinataries (comma separated): ").strip().lower()
            msg = input(f"{username}> Message: ").strip()
            if msg:
                sent = client.send_message(dest, msg)
        try:
            while True:
                message =  client.receive_message()
                if message:
                    if message['metadata']['message_type'] == SRV_LISTALL: 
                        print(f'{username} > {",".join(message["message_content"])}')
                        waiting_for_response = False
                    elif message['metadata']['message_type'] == SRV_DEL_USER:
                        if message['message_content'] == "Success":
                            print(f"User {username} deleted. Closing Connection")
                            client.close()
                            sys.exit()
                    elif message['metadata']['message_type'] == SRV_MSG_FAILURE:
                        print(f"Server Error: {message['message_content']}\nClosing Connection")
                        client.close()
                        sys.exit()
                    elif message['metadata']['message_type'] in [SRV_LOGIN, SRV_SIGNUP]:  
                        waiting_for_response = False
                    
                    else: 
                        print(f'{message["sender_timestamp"][:-3]} {message["sender_username"]} > {message["message_content"]}')
                

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print(f'E1 Reading Error {e}')
                sys.exit()
            continue

            # waiting for response 
        except Exception as e:
            print(traceback.format_exc())
            print(f'E2 Reading error: {e}')
            sys.exit()

            