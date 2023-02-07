import socket
import select
import time

HOST = socket.gethostname()#'65.112.8.28'
HOST = "10.250.227.245"
print(HOST)
PORT = 6000
TIMEOUT = 60 # In seconds

# Request Protocol Definition
# HEADER:
# USERNAME_LENGTH -->  16 byte
# MESSAGE_LENGTH -->  150 byte
# TYPE_REQUEST --> 1 byte
# DATA:
# USERNAME --> 
# MESSAGE -->

# Size of the header that encodes the username size
HDR_USERNAME_SZ = 2
# 
HDR_DESTINATARIES_SZ = 10 
HDR_MESSAGE_SZ = 3
HDR_REQUEST_TYPE_SZ = 1
HDR_SZ = HDR_USERNAME_SZ + HDR_MESSAGE_SZ + HDR_REQUEST_TYPE_SZ


# Reply Protocol Definition
HDR_USERNAME_FROM_SZ = 1


# Stores existing usernames 
# Usernames have a length from 1 to 99 chars
usernames = ['adolfo', 
             'le', 
             'jacobo']

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
        message_type_hdr = scket.recv(HDR_REQUEST_TYPE_SZ)

        # Connection Error 
        if not len(message_type_hdr): 
            print('Error: message type header missing')
            return False 

        message_type = int(message_type_hdr.decode('utf-8').strip())

        # Read username, needed for every message type 
        username_hdr = scket.recv(HDR_USERNAME_SZ)

        # Connection Error
        if not (len(username_hdr)):
            print('Error: username header missing')
            return False


        username_length = int(username_hdr.decode('utf-8').strip())
        username = scket.recv(username_length).decode('utf-8').strip()

        # Username & message type decoded before returned; values used by other functions 
        message_content = {'message_type_hdr': message_type, 
                        'username': username}

        # Login or Signup, only username returned 
        if message_type == 1 or message_type == 2: 
            return message_content
            
        # Message Client Request 
        elif message_type == 3: 

            destinataries_hdr = scket.recv(HDR_DESTINATARIES_SZ)

            # Connection Error
            if not (len(destinataries_hdr)):
                print('Error: destinataries header missing')
                return False

            destinataries_length = int(destinataries_hdr.decode('utf-8').strip())
            destinataries = scket.recv(destinataries_length).decode('utf-8').strip().split(',')

            message_hdr = scket.recv(HDR_MESSAGE_SZ)
            
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
            print(message_content)

            # Create new user in database 
            if message_content['message_type'] == 2: 
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
            time.sleep(5)

            if message_content['message_type'] == 3: 
                for dest_sockt, info in clients.items():
                    if info['username'] in message_content['destinataries']:
                        dest_sockt.send(
                            message_content['username_hdr'] + 
                            message_content['username'].encode('utf-8') + 
                            message_content['message_hdr'] + 
                            message_content['encoded_message'])

                        print(f"Message sent from user {clients[sockt]['username']} to {info['username']}: {message_content['message'].decode('utf-8').strip()}")
                        
                    
                    
               






