import socket
import select
from protocol import *
from utils import * 

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
        # Read metadata 
        metadata = read_metadata_header(scket)
        print(metadata)
        if not metadata: 
            print("metadata read")
            raise Exception("Unable to read metadata")

        message = {'metadata': metadata}

        # Login or Signup, only username returned 
        if metadata['message_type'] in [CL_LOGIN, CL_SIGNUP, CL_DEL_USER]: 
            return message

        elif metadata['message_type'] == CL_LISTALL: 
            filter_length = int(scket.recv(MSG_HDR_SZ).decode('utf-8').strip())
            username_filter = scket.recv(filter_length).decode('utf-8')
            message['username_filter'] = username_filter
            return message    
            
        # Message Client Request 
        elif metadata['message_type'] == CL_SEND_MSG: 

            destinataries_hdr = scket.recv(DESTINATARIES_HDR_SZ)

            # Connection Error
            if not (len(destinataries_hdr)):
                
                raise Exception("Destinataries header missing")

            destinataries_length = int(destinataries_hdr.decode('utf-8').strip())
            destinataries = scket.recv(destinataries_length).decode('utf-8').strip().split(',')

            message_hdr = scket.recv(MSG_HDR_SZ)
            
            # Connection Error
            if not (len(message_hdr)):
                raise Exception("Message header missing")

            message_length = int(message_hdr.decode('utf-8').strip())
            message_content = scket.recv(message_length)

            message['destinataries'] = destinataries
            message['message_hdr'] = message_hdr
            message['encoded_message'] = message_content
            
            return message
  
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
            message = receive_message(conn)
            print('Message Received', message)

            # Login and Signup 
            if message['metadata']['message_type']  == CL_SIGNUP: 
                if message['metadata']['sender_name'] in usernames: 
                    metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                    print("Failed signup attempt") 
                    msg = "Signup failed: username taken." 
                    bmsg = msg.encode('utf-8')
                    bmsg_hdr = f"{len(bmsg):<{MSG_HDR_SZ}}".encode('utf-8')
                    sent = conn.send(metadata_hdr + bmsg_hdr + bmsg)
                    print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 

                else: 
                    usernames.append(message['metadata']['sender_name'])
                    print(f"New user {message['metadata']['sender_name']} added to database") 
            
                    # Add new socket to the list of sockets passed to select
                    socket_list.append(conn)

                    clients[conn] = {'username' : message['metadata']['sender_name'],
                                    'addr': addr}
                    print(f"Accepted new connection from user: {message['metadata']['sender_name']} at {addr[0]}:{addr[1]}")


            elif message['metadata']['message_type']  == CL_LOGIN: 
                if message['metadata']['sender_name'] not in usernames:
                    print("Failed login attempt") 
                    metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                    msg = "Login failed: invalid username" 
                    bmsg = msg.encode('utf-8')
                    bmsg_hdr = f"{len(bmsg):<{MSG_HDR_SZ}}".encode('utf-8')
                    sent = conn.send(metadata_hdr + bmsg_hdr + bmsg)
                    print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 


                else:             
                    # Add new socket to the list of sockets passed to select
                    socket_list.append(conn)

                    clients[conn] = {'username' : message['metadata']['sender_name'],
                                    'addr': addr}


                    print(f"Accepted new connection from user: {message['metadata']['sender_name']} at {addr[0]}:{addr[1]}")
            else: 
                pass # handle this 

        else:
            message = receive_message(sockt)
            if not message:
                print(f"Closed connection from user: {clients[sockt]['username']} at {clients[sockt]['addr'][0]}:{clients[sockt]['addr'][1]}")
                socket_list.remove(sockt)
                del clients[sockt] 
                continue
            print('Message Received', message)

            if message['metadata']['message_type'] == CL_SEND_MSG: 
                # Message server reply 
                for dest_sockt, info in clients.items():
                    if info['username'] in message['destinataries']:
                        print(f"trying to send a message to {info['username']}")
                        metadata_hdr =  create_metadata_header(SRV_FORWARD_MSG, "server")

                        # username of message sender 
                        sender_username = message['metadata']['sender_name']
                        bsender_username = sender_username.encode('utf-8')
                        bsender_username_hdr = f"{len(bsender_username):<{USERNAME_HDR_SZ}}".encode('utf-8')
                        dest_sockt.send(
                            metadata_hdr +
                            bsender_username_hdr + 
                            bsender_username + 
                            message['message_hdr'] +
                            message['encoded_message'])

                        print(f"Message sent from user {clients[sockt]['username']} to {info['username']}: {message['encoded_message'].decode('utf-8').strip()}")
           
            # LISTALL REQUEST
            if message['metadata']['message_type'] == CL_LISTALL: 
                metadata_hdr =  create_metadata_header(SRV_LISTALL, "server")
                filtered_usernames = [name for name in usernames if name.startswith(message['username_filter'])]
                bdest = ",".join(filtered_usernames).encode("utf-8")
                dest_hdr = f"{len(bdest):<{DESTINATARIES_HDR_SZ}}".encode('utf-8')
                sockt.send(
                    metadata_hdr +
                    dest_hdr +
                    bdest
                )

            # DELETE USER REQUEST 
            if message['metadata']['message_type'] == CL_DEL_USER: 
                print(f"Delete user request from user: {clients[sockt]['username']} at {clients[sockt]['addr'][0]}:{clients[sockt]['addr'][1]}")
                socket_list.remove(sockt)
                usernames.remove(clients[sockt]['username'])
                del clients[sockt] 
                print(usernames)
                metadata_hdr =  create_metadata_header(SRV_DEL_USER, "server")
                msg = "Success" 
                bmsg = msg.encode('utf-8')
                bmsg_hdr = f"{len(bmsg):<{MSG_HDR_SZ}}".encode('utf-8')
                sent = sockt.send(metadata_hdr + bmsg_hdr + bmsg)
                print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 


                    
                    
               






