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
import numpy as np 
import time


class QuiplashServicer(object):
    """Interface exported by the server.
    """
    def __init__(self, server_id, primary_ip):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.is_primary = self.ip == primary_ip
        self.primary_ip = primary_ip
        self.server_id = server_id; # testing purposes only; 
        self.stubs = {} 
        self.game_started = False
        self._initialize_storage(); 
        self.num_players = 0

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

    def SendQuestions(self, request, context):
        """Request from primary server 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NotifyPlayers(self, request, context):
        """Server notification 
        """
        print(request.text)
        if request.type == quiplash_pb2.GameNotification.GAME_START: 
            self.game_started = True 
        return quiplash_pb2.RequestReply(reply='Success', 
                                        request_status=quiplash_pb2.SUCCESS) 

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
        self.db.dadd("assignment", (username, {"ip": ip_address, "questions": {}}))
        self.num_players += 1 
        print(f'New player joined {username}, {len(self._get_players())} players in the room')

    def create_stub(self, node_ip_address): 
        if node_ip_address in self.stubs.keys(): 
            print("Error: Stub already exists")
        else: 
            channel = grpc.insecure_channel(f"{node_ip_address}:{os.environ['QUIPLASH_SERVER_PORT']}")
            self.stubs[node_ip_address] = quiplash_pb2_grpc.QuiplashStub(channel)
            #print(f'Created stub to {node_ip_address}')

    def assign_questions(self, mode='all'):
        """
        """
        questions = self.db.get('question_prompt')
        if mode == 'all': 
            question_ids = list(questions.keys())
        elif mode in ['random', 'system']:
            question_ids = [question_id for question_id in questions if questions[question_id]['category'] == mode]
            pass
        else:
            pass

        questions_to_assign = np.random.choice(question_ids, self.num_players)
        np.random.shuffle(questions_to_assign) 
        questions_to_assign = list(questions_to_assign)
        print(type(questions_to_assign))

        questions_to_assign = questions_to_assign + [questions_to_assign[self.num_players-1]] + questions_to_assign[:self.num_players-1]
        print(questions_to_assign)
        assigned_questions = {}
        
        for idx, player in enumerate(self._get_players()):
            print(player)
            player_ip = self.db.dget('assignment', player)[player_ip]
            assigned_questions[player_ip] = (questions_to_assign[idx], questions_to_assign[idx + self.num_players])

            # Handle persistence
            temp = self.db.get("assignment")
            temp[player]["questions"][questions_to_assign[idx]] = {"answer": "No answer", "vote_count":0}
            temp[player]["questions"][questions_to_assign[idx + self.num_players]] = {"answer": "No answer", "vote_count":0}
            self.db.set("assignment", temp)
        
        return assigned_questions
        

    def client_handle(self): 
        # JoinGame routine 
        if not self.is_primary: 
            while True: 
                username = input("Enter username: ").strip().lower()
                user = quiplash_pb2.User(username=username, ip_address=self.ip)
                reply = self.stubs[self.primary_ip].JoinGame(user)
                if reply.request_status == quiplash_pb2.FAILED:
                    print(reply.reply)
                else:
                    break
            print(f"Successfully joined game, username {username}")

            while not self.game_started: 
                time.sleep(0.5)
                continue 
            while self.game_started: 
                continue 
        else: 
            while True: 
                username = input("Enter username: ").strip().lower()
                if username in self._get_players(): 
                    print("Error: username taken")
                else: 
                    self.add_new_player(username, self.ip)
                    break 
            print("\n Once all players have joined the room, press enter to start game \n")
            while True: 
                start_game = input("")
                if start_game == '': 
                    break 
            game_start_text = "Starting the game. Ready... Set.... QUIPLASH"
            print(f"\n {game_start_text} \n")

            self.game_started = True 

            # notifies other players game will begin 
            for ip, stub in self.stubs.items(): 
                notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.GAME_START, text=game_start_text)
                reply = stub.NotifyPlayers(notification)

            assigned_questions = self.assign_questions()

            for ip, stub in self.stubs.items(): 
                player_questions = assigned_questions[ip]
                grpc_question_list = []
                for question_id in player_questions:
                    question = self.db.dget('question_prompt', question_id)
                    print(question)
                    # grpc_question = quiplash_pb2.Question(type)
                
            # return quiplash_pb2.QuestionList(question_list=grpc_question_list)

                
 

            
        
           

def serve(server_id, primary_ip):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    quiplash_servicer = QuiplashServicer(server_id, primary_ip)
    quiplash_pb2_grpc.add_QuiplashServicer_to_server(quiplash_servicer, server)
    
    IP = socket.gethostbyname(socket.gethostname())
    PORT = os.environ['QUIPLASH_SERVER_PORT']
    server.add_insecure_port(f'{IP}:{PORT}')
    server.start()

    # Start the client thread that takes terminal input with gRPC channel and stub
    client_thread = threading.Thread(target=quiplash_servicer.client_handle)
    client_thread.start()

    server.wait_for_termination()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    servers = [1, 2, 3, 4, 5, 6, 7, 8]
    parser.add_argument("--server", "-s", help="Server id", type=int, choices=servers, default=0)
    parser.add_argument("-I", "--primary_ip", help="IP address of primary server", default=socket.gethostbyname(socket.gethostname()))
    args = parser.parse_args()

    serve(args.server, args.primary_ip) 