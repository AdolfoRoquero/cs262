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
from inputimeout import inputimeout



TIME_TO_ANSWER = 10
EMPTY_ANS_DEFAULT = "NA"


def dictToGRPCQuestion(question_dict, question_id):
        assert "category" in question_dict.keys() 
        assert "question" in question_dict.keys()         
        return quiplash_pb2.Question(question_id=question_id, 
                                     question_text=question_dict['question'],
                                     topic=question_dict['category'])

class QuiplashServicer(object):
    """Interface exported by the server.
    """
    def __init__(self):
        self.server_id = 1 
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = os.environ['QUIPLASH_SERVER_PORT']
        self.address = f"{self.ip}:{self.port}"

        # intialize primary ip to your own 
        self.primary_ip = self.ip
        self.primary_port = self.port
        self.primary_address = f"{self.primary_ip}:{self.primary_port}"

        
        self.is_primary = False 
        print(f"Initialize server {self.server_id} ({'PRIMARY' if self.is_primary else 'NOT PRIMARY'}) at {self.address}")

        self.stubs = {}

        self.game_started = False
        self.game_started_cv = threading.Condition()


        self.voting_started = False 


        self._initialize_storage()
        self.num_players = 0

        # if not primary, create stub to primary ip address
        if not self.is_primary: 
            self.create_stub(self.primary_ip, self.primary_port)

        self.unanswered_questions = []
        
    def JoinGame(self, request, context):
        """Request to enter as a User into a game 
        """
        if request.username in self._get_players(): 
            print(f"Error: User {request.username} has already joined")
            return quiplash_pb2.RequestReply(reply='Failure, username taken', 
                                             request_status=quiplash_pb2.FAILED)
        else: 
            # add stub 
            self.create_stub(request.ip_address, request.port)
            self.add_new_player(request.username, request.ip_address, request.port)
            return quiplash_pb2.RequestReply(reply = 'Success', 
                                             request_status=quiplash_pb2.SUCCESS)

    def SendQuestions(self, request, context):
        """Request from primary server 
        """
        for question in request.question_list:
            question_prompt = self.db.dget("question_prompt", question.question_id)
            question_prompt['question_id'] = question.question_id
            self.unanswered_questions.append(question_prompt)
        return quiplash_pb2.RequestReply(reply = 'Success', 
                                                 request_status=quiplash_pb2.SUCCESS)
    
    def SendAnswer(self, request, context):
        """Request from other nodes to primary node with answer to question 
        """
        print(f"Received Anwers from {request.respondent.username}")
        self.add_new_answer(request.respondent.username, request.question_id, request.answer_text)

        # Check if ready to move to voting phase:
        pend_players = self._get_players_pending_ans()
        if len(pend_players) == 0:
            self.voting_started = True
        else:
            print(f"Still Waiting for players {pend_players}\n")


        return quiplash_pb2.RequestReply(reply = 'Success', 
                                         request_status=quiplash_pb2.SUCCESS)

    def NotifyPlayers(self, request, context):
        """Server notification 
        """
        if request.type == quiplash_pb2.GameNotification.GAME_START: 
            self.game_started = True 
            self.game_started_cv.notify()  

        if request.type == quiplash_pb2.GameNotification.VOTING_START: 
            self.voting_started = True 
        
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
    
    def _get_players_pending_ans(self):
        """
        Checks if an answer has been received for all assigned questions to all users
        """
        pending_users = set()
        assignments = self.db.get('assignment')
        for user in assignments:
            for question in assignments[user]['questions']:
                if assignments[user]['questions'][question]['answer'] == EMPTY_ANS_DEFAULT:
                    pending_users.add(user)
        return pending_users
    
    def add_new_player(self, username, ip_address, port): 
        # add username to database 
        self.db.dadd("assignment", (username, {"ip": ip_address, "port": port, "questions": {}}))
        self.num_players += 1 
        print(f'New player joined {username}, {len(self._get_players())} players in the room')

    def add_new_answer(self, username, question_id, answer_text):
        temp = self.db.get("assignment")
        temp[username]["questions"][question_id]['answer'] = answer_text
        self.db.set("assignment", temp)
        

    def create_stub(self, node_ip_address, node_port):
        address = f"{node_ip_address}:{node_port}"
        if address in self.stubs.keys(): 
            print("Error: Stub already exists")
        else: 
            
            channel = grpc.insecure_channel(address)
            self.stubs[address] = quiplash_pb2_grpc.QuiplashStub(channel)
            #print(f'Created stub to {node_ip_address}')

    def assign_questions(self, mode='all'):
        """
        """
        questions = self.db.get('question_prompt')
        if mode == 'all': 
            question_ids = list(questions.keys())
        elif mode in ['random', 'system']:
            question_ids = [question_id for question_id in questions if questions[question_id]['category'] == mode]
        else:
            pass

        questions_to_assign = np.random.choice(question_ids, self.num_players, replace=False)
        np.random.shuffle(questions_to_assign) 
        questions_to_assign = list(questions_to_assign)

        questions_to_assign = questions_to_assign + [questions_to_assign[self.num_players-1]] + questions_to_assign[:self.num_players-1]
        assigned_questions = {}
        
        for idx, player in enumerate(self._get_players()):
            assert questions_to_assign[idx] != questions_to_assign[idx+self.num_players], f"Player {player} is getting the same question ({questions_to_assign[idx]}) twice {questions_to_assign}"
            player_info = self.db.dget('assignment', player)
            player_address = f"{player_info['ip']}:{player_info['port']}"
            assigned_questions[player_address] = (questions_to_assign[idx], questions_to_assign[idx + self.num_players])

            # Handle persistence
            temp = self.db.get("assignment")
            temp[player]["questions"][questions_to_assign[idx]] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
            temp[player]["questions"][questions_to_assign[idx + self.num_players]] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
            self.db.set("assignment", temp)
        
        return assigned_questions
        

    def client_handle(self): 
        pass 
        # # JoinGame routine 
        # if not self.is_primary: 
        #     while True: 
        #         username = input("Enter username: ").strip().lower()
        #         user = quiplash_pb2.User(username=username, 
        #                                  ip_address=self.ip, 
        #                                  port=self.port)
        #         if not username:
        #             print("Error: username cannot be empty")
        #         else:
        #             reply = self.stubs[self.primary_address].JoinGame(user)
        #             if reply.request_status == quiplash_pb2.FAILED:
        #                 print(reply.reply)
        #             else:
        #                 self.username = username
        #                 print(f"Successfully joined game, username {self.username}")
        #                 break

        #     # Wait until game phase starts
        #     while not self.game_started: 
        #         self.game_started_cv.wait()

        #     print("Time to answer questions!!")

        #     for idx, question in enumerate(self.unanswered_questions):
        #         print(f"\n\nQuestion {idx+1}/{len(self.unanswered_questions)}    Topic: {question['category']}")
        #         print(f"{question['question']}\n")
        #         print(f"You have {TIME_TO_ANSWER} seconds to answer!\n")
                
        #         answered = False
        #         try:
        #             # Take timed input using inputimeout() function
        #             answer_text = inputimeout(prompt='Your Answer:\n', timeout=TIME_TO_ANSWER)
        #             answered = True
        #         except Exception:
        #             """Code will enter this code regardless of timeout or not"""
        #             if not answered:
        #                 print("You ran out of time! Moving to next question\n")
                
        #         if answered:
        #             respondent = quiplash_pb2.User(username=self.username)
        #             grpc_answer = quiplash_pb2.Answer(respondent=respondent, 
        #                                               answer_text=answer_text, 
        #                                               question_id=question['question_id']) 
        #             reply = self.stubs[self.primary_address].SendAnswer(grpc_answer)

        #     while not self.voting_started: 
        #         time.sleep(0.5)
        #         continue
        #     print("\n\n\nLet's Vote for funniest answer\n\n\n")



 
        # else: 
        #     while True: 
        #         username = input("Enter username: ").strip().lower()
        #         if username in self._get_players(): 
        #             print("Error: username taken")
        #         elif not username:
        #             print("Error: username cannot be empty")
        #         else: 
        #             self.username = username
        #             self.add_new_player(self.username, self.ip, self.port)
        #             break
        #     print("\n Once all players have joined the room, press enter to start game \n")
        #     while True: 
        #         start_game = input("")
        #         if start_game == '': 
        #             break 
        #     game_start_text = "Starting the game. Ready... Set.... QUIPLASH"
        #     print(f"\n {game_start_text} \n")

        #     self.game_started = True 

        #     # notifies other players game will begin 
        #     for ip, stub in self.stubs.items(): 
        #         notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.GAME_START, text=game_start_text)
        #         reply = stub.NotifyPlayers(notification)

        #     assigned_questions = self.assign_questions()

        #     for address, stub in self.stubs.items(): 
        #         player_questions = assigned_questions[address]
        #         grpc_question_list = []
        #         for question_id in player_questions:
        #             question = self.db.dget('question_prompt', question_id)
        #             grpc_question = dictToGRPCQuestion(question, question_id)
        #             grpc_question_list.append(grpc_question)
        #         reply = stub.SendQuestions(quiplash_pb2.QuestionList(question_list=grpc_question_list))
            

        #     # Wait until voting started flag is set to True
        #     # This flag is set to True once all answers have been received or the has been a timeout
        #     if self.voting_started:
        #         # notifies other players voting phase begins
        #         for ip, stub in self.stubs.items():
        #             print(f"Notify Voting to {ip}") 
        #             notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
        #             reply = stub.NotifyPlayers(notification)

            