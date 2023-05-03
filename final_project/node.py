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
from enum import Enum


def delete_log_files(dir=os.getcwd()):
    for path in os.listdir(dir):
        if path.endswith('.log'):
            os.remove(path)	




TIME_TO_ANSWER = 10
EMPTY_ANS_DEFAULT = "NA"
TIMEOUT_TO_RECEIVE_ANS = 25
STATIC_QUESTIONS_DB = "questions.db"


class LogActionType(Enum):
    """Action types to be used in log"""
    NEW_USER = 'new_user'
    QUESTION_ASS = 'assigned_question'
    ANSWER_RECV = 'answer_received'
    VOTE_RECV = 'vote_received'

class QuiplashServicer(object):
    """Interface exported by the server.
    """
    def __init__(self, ip, port):
        self.server_id = 1; 
        
        self.ip = ip
        self.port = str(port)
        self.address = f"{self.ip}:{self.port}"

        self.primary_ip = ""
        self.primary_port = ""
        self.primary_address = ""
        
        self.is_primary = False
        print(f"Initialize server {self.server_id} ({'PRIMARY' if self.is_primary else 'NOT PRIMARY'}) at {self.address}")

        # Database
        self.db_filename = f'game_state_{self.address}.db' 
        # Log used for replication
        self.pend_log_filename = f'pend_log_{self.address}.log'
        
        # Server event log (monitoring purposes)
        self.server_log_filename = f'server_log_{self.address}.log' 
        self._initialize_storage()

        # stub dictionary, Indexed by address
        self.stubs = {}
        # Map from address to user
        self.address_to_user = {}

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
        self.db.set('assignment', {}) 
        self.db.set('question_prompt', question_prompt_db.get('question_prompt'))


        #
        # Pending log for replication
        #
        
        # Delete previous pending log
        if self.pend_log_filename in os.listdir(dir):
            os.remove(self.pend_log_filename)
        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.pend_log = pickledb.load(self.pend_log_filename, True)
        self.pend_log.set('last_entry', 0)
        self.pend_log.set('current_ptr', 0)
        self.pend_log.set('log', [])

    def _execute_log(self):
        """
        Function to write actions from the pending log into the disk database
        This is the ONLY part of the code that directly writes to db files.

        Function executes all the entries that are pending in the log (keeps track using pointer)
        """
        # Function that loops through unexecuted lines in the log and adds them
        current_ptr = self.pend_log.get('current_ptr')
        last_entry = self.pend_log.get('last_entry')
        log = self.pend_log.get("log")
        
        for entry in log[current_ptr:]:
            params = entry['params']
            if entry['action_type'] == LogActionType.NEW_USER.value:
                self.db.dadd("assignment", (params['username'], {"ip": params['ip'],
                                                                 "port": params['port'], 
                                                                 "questions": {}}))
                self.num_players += 1
                self.address_to_user[f"{params['ip']}:{params['port']}"] = params['username']

            elif entry['action_type'] == LogActionType.QUESTION_ASS.value:
                temp = self.db.get("assignment")
                temp[params['username']]["questions"][params['question_id']] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
                self.db.set("assignment", temp)
                        
            elif entry['action_type'] == LogActionType.ANSWER_RECV.value:
                temp = self.db.get("assignment")
                temp[params['username']]["questions"][params['question_id']]['answer'] = params['answer_text']
                self.db.set("assignment", temp)

            else:
                raise ValueError("Incorrect action type")
            
            # move pointer since you have executed the log command 
            self.pend_log.set('current_ptr', self.pend_log.get('current_ptr') + 1)

    
    def JoinGame(self, request, context):
        """SERVER RUN: Request to enter as a User into a game 
        """
        if request.username in self._get_players(): 
            self.logger.error(f"User {request.username} has already joined")
            return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.FAILED)
        else: 
            # Add to log
            self._add_new_user_to_log(request.username, request.ip_address, request.port)
            for rep_server in self.stubs:
                try: 
                    reply = self.stubs[rep_server].NewUser_StateUpdate(request, timeout=0.5)
                except grpc.RpcError as e:
                    # self.replica_is_alive[rep_server] = False
                    print(f"\t\t Exception: {rep_server} not alive")
            
            # Return existing players such that new joining players can recover the state players. 
            assignments = self.db.get('assignment')
            existing_players = []
            for username in assignments:
                existing_players.append(quiplash_pb2.User(username=username,
                                                          ip_address=assignments[username]['ip'],
                                                          port=assignments[username]['port']))
            
            self.create_stub(request.ip_address, request.port)
            # add stub 
            # TODO execute log / add to db
            # self._execute_log()
            # Persistence Add to db
            self.add_new_player(request.username, request.ip_address, request.port)

            print(f'New player joined {username}, {len(self._get_players())} players in the room')

            return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.SUCCESS,
                                              num_players=self.num_players,
                                              existing_players=existing_players)
        
    def NewUser_StateUpdate(self, request, context):
        """CLIENT RUN: Request to update replica state when a new user JOINS the game.
        """
        self.logger.info(f"STATE UPDT at {self.server_id}: NewUser_StateUpdate User({request.username})")

        if self.is_primary:
            self.logger.error(f"ERROR: STATE UPDT received at {self.server_id} when is_primary = {self.is_primary}")
            raise RuntimeError('Only secondary should receive this state update')
        else :
            # Add to log
            self._add_new_user_to_log(request.username, request.ip_address, request.port)

            self.create_stub(request.ip_address, request.port)
            
            self.add_new_player(request.username, request.ip_address, request.port)
            # TODO
            # Execute pending log entries
            # self._execute_log()

            # TODO
            # Create new stub
            return quiplash_pb2.RequestReply(reply='OK', request_status=quiplash_pb2.SUCCESS)


    def SendQuestions(self, request, context):
        """CLIENT RUN: Request triggered from primary server to other servers
        """
        self.logger.info(f"QUESTIONS RECV: Questions received ({len(request.question_list)}) at {self.address}")
        for question in request.question_list:
            question_prompt = self.db.dget("question_prompt", question.question_id)
            question_prompt['question_id'] = question.question_id

            # Add to local Client Storage
            self.unanswered_questions.append(question_prompt)

        return quiplash_pb2.RequestReply(reply = 'Success', 
                                         request_status=quiplash_pb2.SUCCESS)
    
    
    def QuestionAssignment_StateUpdate(self, request, context):
        """CLIENT RUN: Request to update replica state when a question is ASSIGNED to a user.
        """
        self.logger.info(f"STATE UPDT at {self.server_id}: QuestionAssigment")

        if self.is_primary:
            self.logger.error(f"ERROR: STATE UPDT received at {self.server_id} when is_primary = {self.is_primary}")
            raise RuntimeError('Only secondary should run state updates')
        else :
            for question in request.question_list:
                # Add Question to log
                self._add_question_ass_to_log(question.destinatary.username,
                                              question.question_id)
            # TODO Execute log
        return quiplash_pb2.RequestReply(reply = 'Success', 
                                         request_status=quiplash_pb2.SUCCESS)
    
    
    def SendAnswer(self, request, context):
        """SERVER RUN: Request from other nodes to primary node with answer to question 
        """
        self.logger.info(f"ANSWERS RECV: Received Answer from {request.respondent.username}")

        # Add to log
        self._add_answer_to_log(request.respondent.username, request.question_id, request.answer_text)

        # Send State update to all replicas
        for rep_server in self.stubs:  
            try: 
                reply = self.stubs[rep_server].UserAnswer_StateUpdate(request, timeout=0.5)
                print(reply)
            except grpc.RpcError as e:
                # self.replica_is_alive[rep_server] = False
                print(f"\t\t Exception: {rep_server} not alive")

        # TODO : do with execute_log
        # Persistence on DB
        self.add_new_answer(request.respondent.username, request.question_id, request.answer_text)

        # Check if ready to move to voting phase:
        pend_players = self._get_players_pending_ans()
        if len(pend_players) == 0:
            self.logger.info(f"\tAll anwers received")
            with self.voting_started_cv:
                self.voting_started = True
                self.voting_started_cv.notify_all()
        else:
            self.logger.info(f"\tMissing answers from {request.respondent.username}")

        return quiplash_pb2.RequestReply(reply = 'Success', 
                                         request_status=quiplash_pb2.SUCCESS)
    
    def UserAnswer_StateUpdate(self, request, context):
        """CLIENT RUN Request to update replica state when a user ANSWERS a question.
        """
        self.logger.info(f"STATE UPDT at {self.server_id}: UserAnswer_StateUpdate")
        if self.is_primary:
            self.logger.error(f"ERROR: STATE UPDT received at {self.server_id} when is_primary = {self.is_primary}")
            raise RuntimeError('Only secondary should receive this state update')
        else:
            # Add to log
            self._add_answer_to_log(request.respondent.username, request.question_id, request.answer_text)
            # TODO: make persistence on client
            # self._execute_log()
            return quiplash_pb2.RequestReply(reply='OK', request_status=quiplash_pb2.SUCCESS)

    def NotifyPlayers(self, request, context):
        """CLIENT RUN: Server notification """
        self.logger.info(f"NOTIFICATION RECV: Received Notification at {self.username}")
        if request.type == quiplash_pb2.GameNotification.GAME_START: 
            with self.game_started_cv:
                self.game_started = True 
                self.game_started_cv.notify_all()  

        if request.type == quiplash_pb2.GameNotification.VOTING_START: 
            with self.voting_started_cv:
                self.voting_started = True 
                self.voting_started_cv.notify_all()
        
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

    def Vote_StateUpdate(self, request, context):
        """Request to update replica state when a user VOTES for a quesiton.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    # --------------------------------------------------------------------
    # GETTER HELPER FUNCTIONS
    # --------------------------------------------------------------------
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
    
    def _get_questions_as_grpc_list(self, question_ids, username):
        """
        Converts a list of questions ids addressed to a username
        to a into a list of quiplash_pb2.Question objects
        """
        destinatary = quiplash_pb2.User(username=username)
        question_list = [] 
        for question_id in question_ids:
            question_dict = self.db.dget('question_prompt', question_id)
            grpc_question = quiplash_pb2.Question(question_id=question_id, 
                                                  question_text=question_dict['question'],
                                                  topic=question_dict['category'],
                                                  destinatary=destinatary)
            question_list.append(grpc_question)
        return question_list

    # --------------------------------------------------------------------
    # ADD TO DB (Take from log to DB) 
    # --------------------------------------------------------------------
    def add_new_player(self, username, ip_address, port): 
        # add username to database 
        self.db.dadd("assignment", (username, {"ip": ip_address, "port": port, "questions": {}}))
        self.num_players += 1 
        self.address_to_user[f"{ip_address}:{port}"] = username

    def add_question_ass(self, username, question_id):
        temp = self.db.get("assignment")
        temp[username]["questions"][question_id] = {"answer": EMPTY_ANS_DEFAULT, "vote_count":0}
        self.db.set("assignment", temp)

    def add_new_answer(self, username, question_id, answer_text):
        temp = self.db.get("assignment")
        temp[username]['questions'][question_id]['answer'] = answer_text
        self.db.set("assignment", temp)


    # --------------------------------------------------------------------
    # ADD TO LOG 
    # --------------------------------------------------------------------
    def _add_new_user_to_log(self, username, ip, port):
        self.pend_log.ladd("log", {"action_type": LogActionType.NEW_USER.value, 
                            "params": {"username": username,
                                        "ip": ip,
                                        "port": port}})
        last_entry = self.pend_log.get("last_entry")
        self.pend_log.set("last_entry", last_entry + 1)

    def _add_question_ass_to_log(self, destinatary, question_id):
        self.pend_log.ladd("log", {"action_type": LogActionType.QUESTION_ASS.value, 
                                   "params": {"username": destinatary,
                                              "question_id": question_id}})
        last_entry = self.pend_log.get("last_entry")
        self.pend_log.set("last_entry", last_entry + 1)

    def _add_answer_to_log(self, username, question_id, answer_text):
        self.pend_log.ladd("log", {"action_type": LogActionType.ANSWER_RECV.value, 
                                   "params": {"username": username,
                                              "answer_text": answer_text,
                                              "question_id": question_id}})
        
        last_entry = self.pend_log.get("last_entry")
        self.pend_log.set("last_entry", last_entry + 1)  

    def _add_vote_to_log(self, voter_name, question_id, votee_name):
        self.pend_log.ladd("log", {"action_type": LogActionType.VOTE_RECV.value, 
                                   "params": {"voter": voter_name,
                                              "question_id": question_id,
                                              "votee": votee_name}})
        last_entry = self.pend_log.get("last_entry")
        self.pend_log.set("last_entry", last_entry + 1)


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
        Returns a dictionary of format player_address : [question_id, question_id,  ...]
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

                        print(f" {len(reply.existing_players)} Previously Existing Players")
                        # Add all already existing players
                        for player in reply.existing_players:
                            self._add_new_user_to_log(player.username, player.ip_address, player.port)
                            print("\t", player.username)

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

            assigned_questions = self.assign_questions()
            # Directly persitance to db
            for player_address in assigned_questions:
                username = self.address_to_user[player_address]
                for question_id in assigned_questions[player_address]:
                    self._add_question_ass_to_log(username, question_id)
                    # TODO RUN with execute log
                    self.add_question_ass(username, question_id)

            # 
            # Send Questions to players
            # 
            for address, stub in self.stubs.items(): 
                print(f"Sending questions to {address}")
                player_questions = assigned_questions[address]
                grpc_question_list = self._get_questions_as_grpc_list(player_questions, self.username)
                reply = stub.SendQuestions(quiplash_pb2.QuestionList(question_list=grpc_question_list))

            # State Update for all Client Stubs
            all_question_list = []
            for address, question_ids in assigned_questions.items():
                username = self.address_to_user[address]
                all_question_list += self._get_questions_as_grpc_list(question_ids, username)
            grpc_all_question_list = quiplash_pb2.QuestionList(question_list=all_question_list)
            for stub in self.stubs: 
                state_update_reply = self.stubs[stub].QuestionAssignment_StateUpdate(grpc_all_question_list)

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
            
            print("FIN")
            return 0

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
    if args.port < 50000:
        print(f"Error: port number must be greater than 50000 (current:{args.port})")
        exit()

    serve(args.port) 