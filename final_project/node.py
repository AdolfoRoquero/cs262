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
from collections import defaultdict
import random
import logging



def delete_log_files(dir=os.getcwd()):
    for path in os.listdir(dir):
        if path.endswith('.log'):
            os.remove(path)	




TIME_TO_ANSWER = 10
EMPTY_ANS_DEFAULT = "NA"
TIMEOUT_TO_RECEIVE_ANS = 25

class QuiplashServicer(object):
    """Interface exported by the server.
    """
    def __init__(self, ip, port):
        
        self.server_id = 1
        
        self.ip = ip
        self.port = port
        self.address = f"{self.ip}:{self.port}"

        self.primary_ip = ""
        self.primary_port = ""
        self.primary_address = ""
        
        self.is_primary = False
        print(f"Initialize server {self.server_id} ({'PRIMARY' if self.is_primary else 'NOT PRIMARY'}) at {self.address}")

        self.db_filename = f'game_state_{self.address}.db' 
        self.server_log_filename = f'server_log_{self.address}.db' 
        self._initialize_storage()

        self.stubs = {}
        # # if not primary, create stub to primary ip address
        # if not self.is_primary: 
        #     self.create_stub(self.primary_ip, self.primary_port)

        self.num_players = 0
        self.unanswered_questions = []
        self.answers = []
        self.answers_per_question = defaultdict(lambda: [])

        #
        # Condition variables
        #
        self.game_started = False
        self.game_started_cv = threading.Condition()

        self.voting_started = False 
        self.voting_started_cv = threading.Condition()

        self.sent_answers = False
        self.timer_started = False
        self.scoring_started = False 

    def setup_primary(self):
        self.primary_ip = self.ip
        self.primary_port = self.port
        self.primary_address = f"{self.ip}:{self.port}"
        self.is_primary = True  
    
    def setup_secondary(self):
        pass

    def _initialize_storage(self, dir=os.getcwd()):
        """
        Helper function to initialize disk storage files.
        Sets up all pending log files and db files.

        If the server is rebooting, it will reuse the existing 
        file instead of creating a new one.
        """

        # Delete previous server log
        if self.server_log_filename in os.listdir(dir):
            os.remove(self.server_log_filename)
        
        handler = logging.FileHandler(self.server_log_filename)        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        static_questions_filename = 'questions.db'
        
        # Delete previous database
        if self.db_filename in os.listdir(dir):
            os.remove(self.db_filename)

        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.db = pickledb.load(self.db_filename, True)

        question_prompt_db = pickledb.load(static_questions_filename, True)
        
        self.db.set('question_prompt', question_prompt_db.get('question_prompt'))
        self.db.set('assignment', {}) 

    
    def JoinGame(self, request, context):
        """Request to enter as a User into a game 
        """
        if request.username in self._get_players(): 
            self.logger.error(f"User {request.username} has already joined")
            return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.FAILED)
        else: 
            # add stub 
            self.create_stub(request.ip_address, request.port)
            self.add_new_player(request.username, request.ip_address, request.port)
            return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.SUCCESS,
                                              num_players=self.num_players)

    def SendQuestions(self, request, context):
        """Request triggered from primary server to other servers
        """
        self.logger.info(f"QUESTIONS RECV: Questions received ({len(request.question_list)}) at {self.address}")
        for question in request.question_list:
            question_prompt = self.db.dget("question_prompt", question.question_id)
            question_prompt['question_id'] = question.question_id
            self.unanswered_questions.append(question_prompt)
        return quiplash_pb2.RequestReply(reply = 'Success', 
                                                 request_status=quiplash_pb2.SUCCESS)
    
    # def SendAnswer(self, request, context):
    #     """Request from other nodes to primary node with answer to question 
    #     """
    #     self.logger.info(f"ANSWERS RECV: Received Anwers from {request.respondent.username}")
    #     self.add_new_answer(request.respondent.username, request.question_id, request.answer_text)

    #     # Check if ready to move to voting phase:
    #     pend_players = self._get_players_pending_ans()
    #     if len(pend_players) == 0:
    #         self.logger.info(f"\tAll anwers received")
    #         self.voting_started = True 
    #         for ip, stub in self.stubs.items():
    #             print(f"Notify Voting to {ip}") 
    #             notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
    #             reply = stub.NotifyPlayers(notification)
    #         # with self.voting_started_cv:
    #         #     self.voting_started = True
    #         #     self.voting_started_cv.notify_all()
    #     else:
    #         self.logger.info(f"\tMissing answers from {request.respondent.username}")

    #     return quiplash_pb2.RequestReply(reply = 'Success', 
    #                                      request_status=quiplash_pb2.SUCCESS)

    def SendAnswers(self, request, context):
        """Request from other nodes to primary node with answer to question 
        """
        answers = request.answer_list
        self.logger.info(f"ANSWERS RECV: Received Anwers from {answers[0].respondent.username}")
        for answer in answers: 
            self.add_new_answer(answer.respondent.username, answer.question_id, answer.answer_text)

        # Check if ready to move to voting phase:
        pend_players = self._get_players_pending_ans()
        if len(pend_players) == 0:
            self.logger.info(f"\tAll anwers received")
            self.voting_started = True 
            notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
            for ip, stub in self.stubs.items():
                print(f"Notify Voting to {ip}") 
                reply = stub.NotifyPlayers(notification)
            print("Notified everyone")
            # with self.voting_started_cv:
            #     self.voting_started = True
            #     self.voting_started_cv.notify_all()
        else:
            self.logger.info(f"\tMissing answers from {request.respondent.username}")

        return quiplash_pb2.RequestReply(reply = 'Success', 
                                         request_status=quiplash_pb2.SUCCESS)

    def NotifyPlayers(self, request, context):
        """Server notification 
        """
        self.logger.info(f"NOTIFICATION RECV: Received Notification at {self.username}")
        if request.type == quiplash_pb2.GameNotification.GAME_START: 
            with self.game_started_cv:
                self.game_started = True 
                self.game_started_cv.notify_all()  

        if request.type == quiplash_pb2.GameNotification.VOTING_START: 

            with self.voting_started_cv:
                self.voting_started = True 
                self.voting_started_cv.notify_all()
        
        if request.type == quiplash_pb2.GameNotification.SCORING_START: 
            self.scoring_started = True
        
        return quiplash_pb2.RequestReply(reply='Success', 
                                         request_status=quiplash_pb2.SUCCESS) 
    
    def SendAllAnswers(self, request, context):
        """Request from PRIMARY node to OTHER-NODES with all answers to all questions for voting.
        """
        self.logger.info(f"ALL ANSWERS RECV: Received all anwers ({len(request.answer_list)}) at {self.username}")
    
        for answer in request.answer_list:
            self.answers_per_question[answer.question_id].append({
                'user': answer.respondent.username, 
                'answer': answer.answer_text})
            
            self.answers.append({'user': answer.respondent.username, 
                                 'answer': answer.answer_text, 
                                 'question_id': answer.question_id})
        
        return quiplash_pb2.RequestReply(reply='Success', 
                                         request_status=quiplash_pb2.SUCCESS) 
    def SendVote(self, request, context):
        """Request from OTHER-NODES to PRIMARY node with vote for a given answer 
        """
        self.logger.info(f"VOTE RECV: Vote received from {request.voter.username} to {request.votee.username} on question {request.question_id}")
        # Tally vote count
        temp = self.db.get('assignment')
        temp[request.votee.username]['questions'][request.question_id]['vote_count'] += 1
        self.db.set('assignment', temp)        
        return quiplash_pb2.RequestReply(reply='Success', 
                                         request_status=quiplash_pb2.SUCCESS) 
    
    
    
    def _get_players(self):
        """
        Extracts list of players in db 
        """
        return self.db.get('assignment').keys()
    
    def _get_question_data(self, question_id):
        """
        Extracts question info from static data
        """
        return self.db.dget("question_prompt", question_id)
    
    def _get_players_pending_ans(self):
        """
        Checks if an answer has been received for all assigned questions to all users
        """
        pending_users = set()
        assignments = self.db.get('assignment')
        for user in assignments:
            # TODO: Remover for primary to take part
            if user == self.username:
                continue
            for question in assignments[user]['questions']:
                if assignments[user]['questions'][question]['answer'] == EMPTY_ANS_DEFAULT:
                    pending_users.add(user)
        return pending_users
    
    def _get_answers_as_grpc(self):
        """
        Extracts all answers to all questions from db and 
        compiles them into an AnswersList Object
        """
        answer_list = [] 
        assignments = self.db.get("assignment")
        for user in assignments:
            for question_id in assignments[user]['questions']:
                respondent = quiplash_pb2.User(username=user)
                grpc_answer = quiplash_pb2.Answer(
                    respondent=respondent,
                    answer_text=assignments[user]['questions'][question_id]['answer'],
                    question_id=question_id)
                answer_list.append(grpc_answer)

        return quiplash_pb2.AnswerList(answer_list=answer_list)
    
    def _get_questions_as_grpc_list(self, question_ids):
        """
        Extracts all answers to all questions from db and 
        compiles them into an AnswersList Object
        """
        question_list = [] 
        for question_id in question_ids:
            question_dict = self.db.dget('question_prompt', question_id)
            grpc_question = quiplash_pb2.Question(question_id=question_id, 
                                                  question_text=question_dict['question'],
                                                  topic=question_dict['category'])
            question_list.append(grpc_question)
        return quiplash_pb2.QuestionList(question_list=question_list)
    
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
            self.logger.error(f"ERROR: Stub already exists")
        else: 
            channel = grpc.insecure_channel(address)
            stub = quiplash_pb2_grpc.QuiplashStub(channel)
            try:
                grpc.channel_ready_future(channel).result(timeout=2)
                self.stubs[address] = stub 
                self.logger.info(f"STUB CREATED: Created stub to {address}")
                return True
            except grpc.FutureTimeoutError:
                self.logger.error(f"ERROR: Failed to connect to address {address}")
                return False
        
            

    def assign_questions(self, mode='all'):
        """
        """
        if not self.is_primary: 
            raise RuntimeError("Only primary should run this function") 
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

            # TODO Handle persistence
            temp = self.db.get("assignment")
            temp[player]["questions"][questions_to_assign[idx]] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
            temp[player]["questions"][questions_to_assign[idx + self.num_players]] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
            self.db.set("assignment", temp)

            if player_address == self.address: 
                for question_id in assigned_questions[player_address]:
                    question_prompt = self.db.dget("question_prompt", question_id)
                    question_prompt['question_id'] = question_id
                    self.unanswered_questions.append(question_prompt)
        return assigned_questions
        

    def client_handle(self):
        host_mode = input("Start New Game or Join Existing (1 or 2): ")
        while host_mode not in ['1', '2']:
            print("\nOption must be `1` or `2`\n")
            host_mode = input("Start New Game or Join Existing (1 or 2)")

        if host_mode == '1':
            # Primary Node
            self.setup_primary()



        elif host_mode == '2':
            # Secondary Node
            game_host_address = input("Enter game code: ")
            while not game_host_address or len(game_host_address.split(':')) != 2:
                print("\nCode must be of form `<ip_address>:<port>` \n")
                game_host_address = input("Enter game code: ")
            
            # TODO Check Liveness for correct ip


            self.primary_ip, self.primary_port = game_host_address.split(':')
            self.primary_address = game_host_address
            self.create_stub(self.primary_ip, self.primary_port)


        # JoinGame routine 
        if not self.is_primary: 
            while True: 
                username = input("Enter username: ").strip().lower()
                user = quiplash_pb2.User(username=username, 
                                         ip_address=self.ip, 
                                         port=self.port)
                if not username:
                    print("Error: username cannot be empty")
                else:
                    reply = self.stubs[self.primary_address].JoinGame(user)
                    if reply.request_status == quiplash_pb2.FAILED:
                        print(f"Username {username} taken, try again")
                    else:
                        self.username = username
                        print(f"Successfully joined game, username {self.username}")
                        self.server_id = reply.num_players
                        break

            # Wait until game phase starts
            with self.game_started_cv:
                while not self.game_started:
                    self.game_started_cv.wait() 

            print("Time to answer questions!!")
            for idx, question in enumerate(self.unanswered_questions):
                print(f"\n\nQuestion {idx+1}/{len(self.unanswered_questions)}    Topic: {question['category']}")
                print(f"{question['question']}\n")
                print(f"You have {TIME_TO_ANSWER} seconds to answer!\n")
                
                answered = False
                try:
                    # Take timed input using inputimeout() function
                    answer_text = inputimeout(prompt='Your Answer:\n', timeout=TIME_TO_ANSWER)
                    answered = True
                except Exception:
                    """Code will enter this code regardless of timeout or not"""
                    if not answered:
                        print("You ran out of time! Moving to next question\n")
                
                if answered:
                    respondent = quiplash_pb2.User(username=self.username)
                    grpc_answer = quiplash_pb2.Answer(respondent=respondent, 
                                                      answer_text=answer_text, 
                                                      question_id=question['question_id']) 
                    reply = self.stubs[self.primary_address].SendAnswer(grpc_answer)
            
            # Wait until voting phase starts (Queue is given by Notification from Server)
            with self.voting_started_cv:
                while not self.voting_started:
                    self.voting_started_cv.wait() 

            print("\n\n\nLet's Vote for funniest answer\n\n\n")
            print(self.answers_per_question)
            for idx, question_id in enumerate(self.answers_per_question):
                question_info = self._get_question_data(question_id)
                print(f"Question {idx}:\n")
                print(f"Prompt {question_info['question']}\n\n")
                users_with_answer = []
                for ans_idx, answer in enumerate(self.answers_per_question[question_id]):
                    print(f"Answer {answer['user']} :{answer['answer']}")
                    users_with_answer.append(answer['user'])
                
                answered = False
                try:
                    # Take timed input using inputimeout() function
                    pref_user = inputimeout(prompt='Your favorite answer is:\n', timeout=TIME_TO_ANSWER)
                    answered = True
                except Exception:
                    """Code will enter this code regardless of timeout or not"""
                    if not answered:
                        print("You ran out of time! Moving to next question\n")
                
                if answered and (pref_user in users_with_answer):
                    voter = quiplash_pb2.User(username=self.username)
                    votee = quiplash_pb2.User(username=pref_user)
                    grpc_vote = quiplash_pb2.Vote(voter=respondent, 
                                                  votee=votee,
                                                  question_id=question_id)
                    reply = self.stubs[self.primary_address].SendVote(grpc_vote)
                       
        else: 
            while True: 
                username = input("Enter username: ").strip().lower()
                if username in self._get_players(): 
                    print("Error: username taken")
                elif not username:
                    print("Error: username cannot be empty")
                else: 
                    self.username = username
                    self.add_new_player(self.username, self.ip, self.port)
                    break
            print(f"\n\t\t\t Let others know your code !! \n \t\t\t{self.address} \n")
            print("\n Once all players have joined the room, press enter to start game \n")

            while True: 
                start_game = input("")
                if start_game == '': 
                    break 
            # 
            # Send Questions to players
            # 
            assigned_questions = self.assign_questions()
            for address, stub in self.stubs.items(): 
                print(f"Sending questions to {address}")
                player_questions = assigned_questions[address]
                grpc_question_list = self._get_questions_as_grpc_list(player_questions)
                reply = stub.SendQuestions(grpc_question_list)

            game_start_text = "Starting the game. Ready... Set.... QUIPLASH"
            print(f"\n {game_start_text} \n")

            self.game_started = True 
            # notifies other players game will begin 
            for ip, stub in self.stubs.items(): 
                notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.GAME_START, text=game_start_text)
                reply = stub.NotifyPlayers(notification)
            

            # Wait until voting started flag is set to True if all answers have been received or it timed out
            with self.voting_started_cv:
                while not self.voting_started:
                    self.voting_started_cv.wait(timeout=TIMEOUT_TO_RECEIVE_ANS)
                    self.voting_started = True
                    print("TIMEOUT_OCUURRED")

            # 
            # Send Answers from players to players
            #            
            grpc_answers = self._get_answers_as_grpc()
            for ip, stub in self.stubs.items():
                print(f"Send Answers to {ip}")
                stub.SendAllAnswers(grpc_answers)
            #
            # Notifies other players voting phase begins
            # 
            for ip, stub in self.stubs.items():
                print(f"Notify Voting to {ip}") 
                notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
                reply = stub.NotifyPlayers(notification)
            
        pass
     

def serve(port):
    IP = socket.gethostbyname(socket.gethostname())
    PORT = port
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    quiplash_servicer = QuiplashServicer(IP, PORT)
    quiplash_pb2_grpc.add_QuiplashServicer_to_server(quiplash_servicer, server)
    server.add_insecure_port(f'{IP}:{PORT}')
    server.start()
    # Start the client thread that takes terminal input with gRPC channel and stub
    client_thread = threading.Thread(target=quiplash_servicer.client_handle)
    client_thread.start()

    server.wait_for_termination()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    servers = [1, 2, 3, 4, 5, 6, 7, 8]
    parser.add_argument("-P", "--port", help="Port of where server will be running", type=int, default=os.environ['QUIPLASH_SERVER_PORT'])
    args = parser.parse_args()
        #     # Wait until voting started flag is set to True
        #     # This flag is set to True once all answers have been received or the has been a timeout
        #     if self.voting_started:
        #         # notifies other players voting phase begins
        #         for ip, stub in self.stubs.items():
        #             print(f"Notify Voting to {ip}") 
        #             notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
        #             reply = stub.NotifyPlayers(notification)

    serve(args.port) 
