from copyreg import pickle
from unicodedata import name
from urllib import request
import grpc 
import quiplash_pb2
import quiplash_pb2_grpc
from concurrent import futures
import pickledb 
import os 
import argparse
import socket
import threading
from client import client_handle


class QuiplashServicer(object):
    """Interface exported by the server.
    """
    def __init__(self, server_id, primary_ip):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.is_primary = self.ip == primary_ip
        self.primary_ip = primary_ip
        self.server_id = server_id; # testing purposes only; 
        self.stubs = {} 
        self._initialize_storage(); 

        # if not primary, create stub to primary ip address
        if not self.is_primary: 
            self.create_stub(self.primary_ip)
        else: 
            print(f'Primary server running with IP: {self.primary_ip}')

    def JoinGame(self, request, context):
        """Request to enter as a User into a game 
        """
        username = request.username 
        if username in self._get_players(): 
            print(f"Error: User {username} has already joined")
            return quiplash_pb2.RequestReply(reply='Failure, username taken', 
                                                 request_status=quiplash_pb2.FAILED)
        else: 
            # add stub 
            self.create_stub(request.ip_address)
            self.add_new_player(request.username, request.ip_address)
            return quiplash_pb2.RequestReply(reply = 'Success', 
                                                 request_status=quiplash_pb2.SUCCESS)

    def AskQuestion(self, request, context):
        """Request from primary server 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NotifyPlayers(self, request, context):
        """Server notification 
        """
        print(request.text)

    def _initialize_storage(self, dir=os.getcwd()):
        """
        Helper function to initialize disk storage files.
        Sets up all pending log files and db files.

        If the server is rebooting, it will reuse the existing 
        file instead of creating a new one.
        """
        
        static_questions_filename = 'questions.db'
        db_filename = 'game_state_' + str(self.server_id) + '.db' 
        
        # Delete previous database
        if db_filename in os.listdir(dir):
            os.remove(db_filename)

        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.db = pickledb.load(db_filename, True)

        question_prompt_db = pickledb.load(static_questions_filename, True)
        
        self.db.set('question_prompt', question_prompt_db.get('question_prompt'))

        self.db.set('assignment', {})
    
    def _get_players(self):
        """
        Extracts list of players in db 
        """
        return self.db.get('assignment').keys()
    
    def add_new_player(self, username, ip_address): 
        # add username to database 
        self.db.dadd("assignment", (username, {"ip": ip_address}))
        print(f'New player joined {username}, {len(self._get_players())} players in the room')

    def create_stub(self, node_ip_address): 
        if node_ip_address in self.stubs.keys(): 
            print("Error: Stub already exists")
        else: 
            channel = grpc.insecure_channel(f"{node_ip_address}:{os.environ['QUIPLASH_SERVER_PORT']}")
            self.stubs[node_ip_address] = quiplash_pb2_grpc.QuiplashStub(channel)
            #print(f'Created stub to {node_ip_address}')

    

def serve(server_id, primary_ip):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    quiplash_servicer = QuiplashServicer(server_id, primary_ip)
    quiplash_pb2_grpc.add_QuiplashServicer_to_server(quiplash_servicer, server)
    
    IP = socket.gethostbyname(socket.gethostname())
    PORT = os.environ['QUIPLASH_SERVER_PORT']
    server.add_insecure_port(f'{IP}:{PORT}')
    server.start()

    # Start the client thread that takes terminal input with gRPC channel and stub
    client_thread = threading.Thread(target=client_handle, args=(quiplash_servicer,))
    client_thread.start()


    server.wait_for_termination()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    servers = [1, 2, 3, 4, 5, 6, 7, 8]
    parser.add_argument("--server", "-s", help="Server id", type=int, choices=servers, default=0)
    parser.add_argument("-I", "--primary_ip", help="IP address of primary server", default=socket.gethostbyname(socket.gethostname()))
    args = parser.parse_args()

    serve(args.server, args.primary_ip) 