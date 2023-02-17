import socket
import select
from collections import defaultdict
from protocol import *
from utils import * 



class Server():
    def __init__(self, host='10.0.20.87', 
                       port=6000, 
                       timeout=60, 
                       usernames=["Leticia", "Liz", "Bel"],
                       clients={},
                       pending_messages=defaultdict(list)):
        
        self.host = host
        print(host)
        self.port = port
        self.timeout = timeout

        # Stores existing usernames 
        # Usernames have a length from 1 to 99 chars
        self.usernames = usernames
        # Key: socket, val: {username: , addr:}
        self.clients = clients
        # store pending messages 
        # Key: username, val: [message]
        self.pending_messages = pending_messages

    
    def setup(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.socket_list = [self.server_socket]

    def run(self):
        while True:
            ready_to_read, ready_to_write, in_error = select.select(
                            self.socket_list,
                            self.socket_list,
                            [],
                            self.timeout)
        
            for sockt in ready_to_read:

                # Accept new connections for server socket
                if sockt == self.server_socket:
                    # Create new socket for send/receive from client
                    conn, addr = self.server_socket.accept()
                    print(conn, addr)
                    message = self.receive_message(conn)
                
                    # Login and Signup 
                    if message['metadata']['message_type']  == CL_SIGNUP: 
                        if message['metadata']['sender_name'] in self.usernames: 
                            metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                            print("Failed signup attempt") 
                            msg_enc = encode_message_segment("Signup failed: username taken.", MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)
                            print('Message sent, %d bytes transmitted' % (sent)) 

                        else: 
                            # Reply to client successfull connection 
                            metadata_hdr = create_metadata_header(SRV_SIGNUP, "server")
                            msg = "Signup successful!" 
                            msg_enc = encode_message_segment(msg, MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)

                            self.usernames.append(message['metadata']['sender_name'])
                            print(f"New user {message['metadata']['sender_name']} added to database") 
                    
                            # Add new socket to the list of sockets passed to select
                            self.socket_list.append(conn)

                            self.clients[conn] = {'username' : message['metadata']['sender_name'],
                                            'addr': addr}
                            print(f"Accepted new connection from user: {message['metadata']['sender_name']} at {addr[0]}:{addr[1]}")


                    elif message['metadata']['message_type']  == CL_LOGIN: 
                        if message['metadata']['sender_name'] not in self.usernames:
                            print("Failed login attempt") 
                            metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                            msg = "Login failed: invalid username" 
                            msg_enc = encode_message_segment(msg, MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)
                            print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 

                        else:             
                            # Reply to client successfull connection 
                            metadata_hdr = create_metadata_header(SRV_LOGIN, "server")
                            msg = "Login successful!" 
                            msg_enc = encode_message_segment(msg, MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)

                            # Add new socket to the list of sockets passed to select
                            self.socket_list.append(conn)

                            self.clients[conn] = {'username' : message['metadata']['sender_name'],
                                            'addr': addr}

                            print(f"Accepted new connection from user: {message['metadata']['sender_name']} at {addr[0]}:{addr[1]}")

                            for pending_msg in self.pending_messages[self.clients[conn]['username']]:
                                metadata_hdr =  create_metadata_header(SRV_FORWARD_MSG, "server")
                                sent = conn.send(metadata_hdr + pending_msg)
                                print('Message sent, %d/%d bytes transmitted' % (sent, len(pending_msg))) 
                        
                            del self.pending_messages[self.clients[conn]['username']]
                    else: 
                        pass # handle this 

                else:
                    message = self.receive_message(sockt)
                    if not message:
                        print(f"Closed connection from user: {self.clients[sockt]['username']} at {self.clients[sockt]['addr'][0]}:{self.clients[sockt]['addr'][1]}")
                        self.socket_list.remove(sockt)
                        del self.clients[sockt] 
                        continue
                    print('Message Received', message)

                    if message['metadata']['message_type'] == CL_SEND_MSG: 
                        # Message server reply 
                        for destinatary in message['destinataries']:
                            if destinatary in self.usernames: 
                                dest_sockets = [client for client in self.clients if self.clients[client]['username'] == destinatary]
                                
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

                                        print(f"Message sent from user {self.clients[sockt]['username']} to {destinatary}: {message['encoded_message'].decode('utf-8').strip()}")
                                else: 
                                    self.pending_messages[destinatary].append(message_body)
                    # LISTALL REQUEST
                    if message['metadata']['message_type'] == CL_LISTALL: 
                        metadata_hdr =  create_metadata_header(SRV_LISTALL, "server")
                        filtered_usernames = ",".join([name for name in self.usernames if name.startswith(message['username_filter'])])
                        dest_enc = encode_message_segment(filtered_usernames, DESTINATARIES_HDR_SZ)                
                        sent = sockt.send(
                            metadata_hdr +
                            dest_enc 
                        )
                        print('Message sent, %d bytes transmitted' % (sent)) 

                    # DELETE USER REQUEST 
                    if message['metadata']['message_type'] == CL_DEL_USER: 
                        print(f"Delete user request from user: {self.clients[sockt]['username']} at {self.clients[sockt]['addr'][0]}:{self.clients[sockt]['addr'][1]}")
                        self.socket_list.remove(sockt)
                        self.usernames.remove(self.clients[sockt]['username'])
                        if self.clients[sockt]['username'] in self.pending_messages:
                            del self.pending_messages[self.clients[sockt]['username']]
                        del self.clients[sockt] 
                        metadata_hdr =  create_metadata_header(SRV_DEL_USER, "server")
                        msg_enc = encode_message_segment("Success", MSG_HDR_SZ)
                        sent = sockt.send(metadata_hdr + msg_enc)
                        print('Message sent, %d bytes transmitted' % (sent)) 


    @staticmethod
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
    server = Server()
    server.setup()
    server.run()
    