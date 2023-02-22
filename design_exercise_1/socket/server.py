import socket
import select
from collections import defaultdict
from protocol import *
from utils import * 
import fnmatch
import os


class SocketServer():
    """
    A class used to represent a Server using sockets for message sending.

    Attributes
    ----------
    host : str
        IP address in which the server is running
    port : int
        Port number used for communication with server
    timeout : int
        Timeout in secondes for the select.select (default is 60)
    usernames : list of str
        list of usernames that have an account
    clients : dict of socket: {username:, addr:}
        dictionary of all connected sockets
    pending_messages : dict of {username: [message]}
        dictionary that, for every username, lists the pending messages that have not been forwarded
    
    Methods
    -------
    setup()
        Creates listening Socket for the server communication.
    run()


    """


    def __init__(self, host, 
                       port, 
                       timeout=60, 
                       usernames=[],
                       clients={},
                       pending_messages=defaultdict(list)):
        """
        Initializes all the class attributes.

        """

        self.host = host
        self.port = int(port)
        self.timeout = timeout

        # Stores existing usernames 
        # Usernames have a length from 1 to 99 chars
        self.usernames = usernames + ['ROOT']
        # Stores connected sockets    
        self.clients = clients
        # store pending messages 
        self.pending_messages = pending_messages

        print(f'Running server on host {host}:{port}')


    
    def setup(self):
        """
        Creates listening Socket for the server communication.

        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.socket_list = [self.server_socket]

    def run(self):
        """
        Continously runs server process to handle messages recieved from the clients


        Raises
        ------
        NotImplementedError
            If no sound is set for the animal or passed in as a
            parameter.
        """
        while True:
            # Determine which sockets have content (ready to read)
            ready_to_read, ready_to_write, in_error = select.select(
                            self.socket_list,
                            self.socket_list,
                            [],
                            self.timeout)
        
            # Handle each ready socket
            for sockt in ready_to_read:

                # Accept new connections for server socket
                if sockt == self.server_socket:
                    # Create new socket for send/receive from client
                    conn, addr = self.server_socket.accept()

                    message = self.receive_message(conn)
                
                    # Client Request to signup a new user
                    if message['metadata']['message_type']  == CL_SIGNUP:
                        
                        # Check that the username is not already in use
                        if message['metadata']['sender_name'] in self.usernames: 
                            metadata_hdr = create_metadata_header(SRV_MSG_FAILURE, "server")
                            print(f"Failed signup attempt with username {message['metadata']['sender_name']}") 
                            msg_enc = encode_message_segment("Signup failed: username taken.", MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)

                            print('Message sent, %d bytes transmitted' % (sent)) 

                        else: 
                            # Reply to client when sign up is successful 
                            metadata_hdr = create_metadata_header(SRV_SIGNUP, "server")
                            msg = "Signup successful!" 
                            msg_enc = encode_message_segment(msg, MSG_HDR_SZ)
                            sent = conn.send(metadata_hdr + msg_enc)

                            self.usernames.append(message['metadata']['sender_name'])
                    
                            # Add new socket to the list of sockets to check for received messages (passed to select.select)
                            self.socket_list.append(conn)

                            # Create a new connection for the username 
                            self.clients[conn] = {'username' : message['metadata']['sender_name'],
                                                  'addr': addr}

                            print(f"New user {message['metadata']['sender_name']} added to database using connection at {addr[0]}:{addr[1]}") 

                    # Client request to login
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
                    
                    # Client Request to send a message
                    if message['metadata']['message_type'] == CL_SEND_MSG: 
                        for destinatary in message['destinataries']:
                            if destinatary in self.usernames: 
                                # Send message to all the client sockets that the destinatary is logged in at. 
                                dest_sockets = [client for client in self.clients if self.clients[client]['username'] == destinatary]
                                
                                # Username of message sender 
                                sender_username_enc = encode_message_segment(message['metadata']['sender_name'], USERNAME_HDR_SZ)

                                # timestamp message sent by client 
                                sender_timestamp_enc = encode_message_segment(message['metadata']['timestamp'], TIMESTAMP_HDR_SZ)

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
                                    # Messages that are destined to users that are not logged in
                                    self.pending_messages[destinatary].append(message_body)

                    # Client Request to list all users
                    if message['metadata']['message_type'] == CL_LISTALL: 
                        metadata_hdr =  create_metadata_header(SRV_LISTALL, "server")
                        if message['username_filter']:
                            listed_usernames = ",".join([name for name in self.usernames if fnmatch.fnmatch(name, message['username_filter'])])
                        else:
                            listed_usernames = ",".join(self.usernames)
                        
                        dest_enc = encode_message_segment(listed_usernames, DESTINATARIES_HDR_SZ)                
                        sent = sockt.send(
                            metadata_hdr +
                            dest_enc
                        )
                        print('Message sent, %d bytes transmitted' % (sent)) 

                    # Client Request to delete its account
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
        """
        Read message from specific socket that is ready to be read from
        (according to select.select)


        Parameters
        ----------
        skcet : socket.Socket
            The socket that is ready to be read from
        """
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
                
            # Client Request to send a message to a destinatary
            elif metadata['message_type'] == CL_SEND_MSG: 
                # Read destinataries 
                destinataries_str = unpack_message_segment(scket, DESTINATARIES_HDR_SZ)

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
    server = SocketServer(host=os.environ['CHAT_APP_SERVER_HOST'],
                          port=os.environ['CHAT_APP_SERVER_PORT'])
    server.setup()
    server.run()
    