import socket
import select
import time
from protocol import *

HOST = socket.gethostname()#'65.112.8.28'
HOST = "10.250.227.245"
PORT = 6000
TIMEOUT = 60 # In seconds

# Stores existing usernames 
# Usernames have a length from 1 to 99 chars
usernames = []

# Key: socket, val: {username: , addr:}
clients = {}

def server_setup():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    return server_socket

def receive_message(scket):
    try:
        # Read type of message 
        message_type_hdr = scket.recv(MSG_TYPE_HDR_SZ)

        # Connection Error 
        if not len(message_type_hdr): 
            print('Error: message type header missing')
            return False 

        message_type = message_type_hdr.decode('utf-8').strip()

        # Read username, needed for every message type 
        username_hdr = scket.recv(USERNAME_HDR_SZ)

        # Connection Error
        if not (len(username_hdr)):
            print('Error: username header missing')
            return False


        username_length = int(username_hdr.decode('utf-8').strip())
        username = scket.recv(username_length).decode('utf-8').strip()

        # Username & message type decoded before returned; values used by other functions 
        message_content = {'message_type': message_type, 
                        'username_hdr': username_hdr,
                        'username': username}

        # Login or Signup, only username returned 
        if message_type in [CL_LOGIN, CL_SIGNUP]: 
            return message_content

        elif message_type == CL_LISTALL: 
            filter_length = int(scket.recv(MSG_HDR_SZ).decode('utf-8').strip())
            username_filter = scket.recv(filter_length).decode('utf-8')
            message_content['username_filter'] = username_filter
            return message_content
            
        # Message Client Request 
        elif message_type == CL_SEND_MSG: 

            destinataries_hdr = scket.recv(DESTINATARIES_HDR_SZ)

            # Connection Error
            if not (len(destinataries_hdr)):
                print('Error: destinataries header missing')
                return False

            destinataries_length = int(destinataries_hdr.decode('utf-8').strip())
            destinataries = scket.recv(destinataries_length).decode('utf-8').strip().split(',')

            message_hdr = scket.recv(MSG_HDR_SZ)
            
            # Connection Error
            if not (len(message_hdr)):
                print('Error: message header missing')
                return False

            message_length = int(message_hdr.decode('utf-8').strip())
            message = scket.recv(message_length)

            message_content['destinataries'] = destinataries
            message_content['message_hdr'] = message_hdr
            message_content['encoded_message'] = message
            
            return message_content

        else: 
            print('Error: unrecognized message type')
            return False  
  
    except Exception as e:
        print('exception', e)
        return False

if __name__ == '__main__':
 server_socket = server_setup()
 socket_list = [server_socket]

 while True:
    ready_to_read, ready_to_write, in_error = select.select(
                    socket_list,
                    socket_list,
                    [],
                    TIMEOUT)
  
    for sockt in ready_to_read:

        # Accept new connections for server socket
        if sockt == server_socket:
            # Create new socket for send/receive from client
            conn, addr = server_socket.accept()
            print(conn, addr)
            message_content = receive_message(conn)
            print('Message Received', message_content)

            # Create new user in database 
            if message_content['message_type'] == CL_SIGNUP: 
                usernames.append(message_content['username'])
                print(f"New user {message_content['username']} added to database") 

            # Add new socket to the list of sockets passed to select
            socket_list.append(conn)

            clients[conn] = {'username' : message_content['username'],
                             'addr': addr}

            print(f"Accepted new connection from user: {message_content['username']} at {addr[0]}:{addr[1]}")

        else:
            message_content = receive_message(sockt)
            if not message_content:
                print(f"Closed connection from user: {clients[sockt]['username']} at {clients[sockt]['addr'][0]}:{clients[sockt]['addr'][1]}")
                socket_list.remove(sockt)
                del clients[sockt] 
                continue
            print('Message Received', message_content)

            if message_content['message_type'] == CL_SEND_MSG: 
                # Message server reply 
                outbound_message_type = f"{SRV_FORWARD_MSG:<{MSG_TYPE_HDR_SZ}}".encode('utf-8')  

                for dest_sockt, info in clients.items():
                    if info['username'] in message_content['destinataries']:
                        print(f"trying to send a message to {info['username']}")
                        dest_sockt.send(
                            outbound_message_type + 
                            message_content['username_hdr'] + 
                            message_content['username'].encode('utf-8') + 
                            message_content['message_hdr'] + 
                            message_content['encoded_message'])

                        print(f"Message sent from user {clients[sockt]['username']} to {info['username']}: {message_content['encoded_message'].decode('utf-8').strip()}")
           
            # LISTALL REQUEST
            if message_content['message_type'] == CL_LISTALL: 
                outbound_message_type = f"{SRV_LISTALL:<{MSG_TYPE_HDR_SZ}}".encode('utf-8')
                filtered_usernames = [name for name in usernames if name.startswith(message_content['username_filter'])]
                bdest = ",".join(filtered_usernames).encode("utf-8")
                dest_hdr = f"{len(bdest):<{DESTINATARIES_HDR_SZ}}".encode('utf-8')
                sockt.send(
                    outbound_message_type +
                    dest_hdr +
                    bdest
                )


                    
                    
               






