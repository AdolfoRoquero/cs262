import socket
import select
from collections import defaultdict
from protocol import *
from utils import * 

HOST = socket.gethostname()#'65.112.8.28'
# HOST = "10.250.227.245"
PORT = 6000
TIMEOUT = 60 # In seconds

# Stores existing usernames 
# Usernames have a length from 1 to 99 chars
usernames = ["Leticia", "Liz", "Bel"]

# Key: socket, val: {username: , addr:}
clients = {}

# store pending messages 
# Key: username, val: [message]
pending_messages = defaultdict(list)

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
        if not metadata: 
            return False            
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
            # Read destinataries 
            destinataries_str = unpack_from_header(scket, DESTINATARIES_HDR_SZ)

            if not destinataries_str: 
                return False 
            destinataries = destinataries_str.strip().split(',')

            message_hdr = scket.recv(MSG_HDR_SZ)
            
            # Connection Error
            if not (len(message_hdr)):
                return False

            message_length = int(message_hdr.decode('utf-8').strip())
            message_content = scket.recv(message_length)

            message['destinataries'] = destinataries
            message['message_hdr'] = message_hdr
            message['encoded_message'] = message_content
            message['message_timestamp'] = metadata['timestamp']
            
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
            
                # Login and Signup 
                if message['metadata']['message_type']  == CL_SIGNUP: 
                    if message['metadata']['sender_name'] in usernames: 
                        metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                        print("Failed signup attempt") 
                        msg_enc = encode_message_segment("Signup failed: username taken.", MSG_HDR_SZ)
                        sent = conn.send(metadata_hdr + msg_enc)
                        print('Message sent, %d bytes transmitted' % (sent)) 

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
                        msg_enc = encode_message_segment(msg, MSG_HDR_SZ)
                        sent = conn.send(metadata_hdr + msg_enc)
                        print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 

                    else:             
                        # Add new socket to the list of sockets passed to select
                        socket_list.append(conn)

                        clients[conn] = {'username' : message['metadata']['sender_name'],
                                        'addr': addr}

                        print(f"Accepted new connection from user: {message['metadata']['sender_name']} at {addr[0]}:{addr[1]}")

                        for pending_msg in pending_messages[clients[conn]['username']]:
                            metadata_hdr =  create_metadata_header(SRV_FORWARD_MSG, "server")
                            sent = conn.send(metadata_hdr + pending_msg)
                            print('Message sent, %d/%d bytes transmitted' % (sent, len(pending_msg))) 
                        
                        del pending_messages[clients[conn]['username']]
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
                    for destinatary in message['destinataries']:
                        if destinatary in usernames: 
                            dest_sockets = [client for client in clients if clients[client]['username'] == destinatary]
                            
                            # username of message sender 
                            sender_username_enc = encode_message_segment(message['metadata']['sender_name'], USERNAME_HDR_SZ)

                            # timestamp message sent by client 
                            sender_timestamp = message['metadata']['timestamp']
                            sender_timestamp_enc = encode_message_segment(message['metadata']['timestamp'], TIMESTAMP_SZ)

                            message_body = (sender_username_enc +
                                            sender_timestamp_enc +
                                            message['message_hdr'] +
                                            message['encoded_message'])
                            if dest_sockets: 
                                for dest_sockt in dest_sockets: 
                                    metadata_hdr = create_metadata_header(SRV_FORWARD_MSG, "server")
                                    dest_sockt.send(metadata_hdr + message_body)

                                    print(f"Message sent from user {clients[sockt]['username']} to {destinatary}: {message['encoded_message'].decode('utf-8').strip()}")
                            else: 
                                pending_messages[destinatary].append(message_body)
                # LISTALL REQUEST
                if message['metadata']['message_type'] == CL_LISTALL: 
                    metadata_hdr =  create_metadata_header(SRV_LISTALL, "server")
                    filtered_usernames = ",".join([name for name in usernames if name.startswith(message['username_filter'])])
                    dest_enc = encode_message_segment(filtered_usernames, DESTINATARIES_HDR_SZ)                
                    sent = sockt.send(
                        metadata_hdr +
                        dest_enc 
                    )
                    print('Message sent, %d bytes transmitted' % (sent)) 

                # DELETE USER REQUEST 
                if message['metadata']['message_type'] == CL_DEL_USER: 
                    print(f"Delete user request from user: {clients[sockt]['username']} at {clients[sockt]['addr'][0]}:{clients[sockt]['addr'][1]}")
                    socket_list.remove(sockt)
                    usernames.remove(clients[sockt]['username'])
                    if clients[sockt]['username'] in pending_messages:
                        del pending_messages[clients[sockt]['username']]
                    del clients[sockt] 
                    metadata_hdr =  create_metadata_header(SRV_DEL_USER, "server")
                    msg_enc = encode_message_segment("Success", MSG_HDR_SZ)
                    sent = sockt.send(metadata_hdr + msg_enc)
                    print('Message sent, %d bytes transmitted' % (sent)) 


                        
                        
                






