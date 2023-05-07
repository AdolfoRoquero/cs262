from copyreg import pickle
from unicodedata import name
import grpc 
import quiplash_pb2
import quiplash_pb2_grpc
from concurrent import futures
import pickledb 
import os 
import argparse
import socket
import threading
import numpy as np 
import time
from inputimeout import inputimeout, TimeoutOccurred
from collections import defaultdict
import random
import logging
from enum import Enum
from utils import check_valid_ip_format
import sys


def delete_log_files(dir=os.getcwd()):
    for path in os.listdir(dir):
        if path.endswith('.log'):
            os.remove(path)	


TIME_PER_ANSWER = 20
TIME_PER_VOTE = 15
EMPTY_ANS_DEFAULT = "NA"
STATIC_QUESTIONS_DB = "questions.db"
QUESTIONS_PER_PLAYER = 2

def liveness_check_thread(instance):
    while True:
        for rep_server_address in instance.stubs: 
            if rep_server_address != instance.address: 
                stub = instance.stubs[rep_server_address]
                try:
                    response = stub.CheckLiveness(quiplash_pb2.LivenessRequest(), timeout=0.5)
                    instance.replica_is_alive[rep_server_address] = True
                except grpc.RpcError as e:
                    instance.replica_is_alive[rep_server_address] = False
                    instance.logger.error(f"ERROR: Liveness check failed between {instance.address_to_user[instance.address]} ({instance.address}) and {instance.address_to_user[rep_server_address]} ({rep_server_address})")
                    if rep_server_address == instance.primary_address: 
                       
                        alive_reps = [rep for rep in instance.replica_is_alive if instance.replica_is_alive[rep]]
                        alive_reps.append(instance.address)

                        # Update primary address to be the next alive replica
                        instance.primary_address = min(alive_reps)
                        instance.primary_ip, instance.primary_port = instance.primary_address.split(":")
                        instance.is_primary = instance.primary_address == instance.address
                        instance.logger.info(f"Primary server changed to {instance.primary_address}")
                        print(f"Primary server changed to {instance.primary_address}")

        time.sleep(2)


class LogActionType(Enum):
    """Action types to be used in log"""
    NEW_USER = 'new_user'
    QUESTION_ASS = 'assigned_question'
    ANSWER_RECV = 'answer_received'
    VOTE_RECV = 'vote_received'

class QuiplashServicer(object):
    """
    Interface exported by the server.
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

        # Database
        self.db_filename = f'game_state_{self.address}.db' 
        # Log used for replication
        self.pend_log_filename = f'pend_log_{self.address}.log'
        
        # Server event log (monitoring purposes)
        self.server_log_filename = f'server_log_{self.address}.log' 
        self._initialize_storage()

        # stub dictionary, Indexed by address
        self.stubs = {}
        # Check if replica is alive for each stub (Indexed by address)
        self.replica_is_alive = {} 

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

        self.voting_started_prim = False 
        self.voting_started_prim_cv = threading.Condition()
        self.voting_started = False 
        self.voting_started_cv = threading.Condition()
       
        self.vote_tallying_started_prim = False 
        self.vote_tallying_started_prim_cv = threading.Condition()
        self.vote_tallying_started = False 
        self.vote_tallying_started_cv = threading.Condition()

    def setup_primary(self):
        self.primary_ip = self.ip
        self.primary_port = self.port
        self.primary_address = f"{self.ip}:{self.port}"
        self.is_primary = True  
    
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
                self.replica_is_alive[address] = True
                self.logger.info(f"STUB CREATED: Created stub to {address}")
                return True
            except grpc.FutureTimeoutError:
                self.logger.error(f"ERROR: Failed to connect to address {address}")
                return False

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


        # Pending log (for replication)
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
                self.add_new_player(params['username'], params['ip'], params['port'])
            elif entry['action_type'] == LogActionType.QUESTION_ASS.value:
                assert ('username' in params) and ('question_id' in params)
                self.add_question_ass(params['username'], params['question_id'])                        
            elif entry['action_type'] == LogActionType.ANSWER_RECV.value:
                self.add_new_answer(params['username'],params['question_id'],params['answer_text'])
            elif entry['action_type'] == LogActionType.VOTE_RECV.value:
                self.add_new_vote(params['voter'], params['votee'],params['question_id'])
            else:
                raise ValueError("Incorrect action type")
            # move pointer since you have executed the log command 
            self.pend_log.set('current_ptr', self.pend_log.get('current_ptr') + 1)

    
    def JoinGame(self, request, context):
        """
        Receives a request to join the game from the SECONDARY node.
        Enters a new user into the game.

        Running host:
        -------------
        Code in this function runs on PRIMARY node (called in SECONDARY).

        Parameters
        ----------
        request: User (quiplash.proto)
            User (with username) that is attempting to join the game.
        
        Returns
        -------
        RequestReply:
            Confirms receipt of the join request by the PRIMARY node.
            Fails if the username is taken
            Upon success, returns the list of existing users.
        """
        if self.is_primary:
            game_status = quiplash_pb2.JoinGameReply.STARTED if self.game_started else quiplash_pb2.JoinGameReply.WAITING
            if request.username in self._get_players(): 
                self.logger.error(f"User {request.username} has already joined")
                return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.FAILED, game_status=game_status)
            else: 
                if self.game_started: 
                    return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.FAILED, game_status=game_status)

                # Add to log
                self._add_new_user_to_log(request.username, request.ip_address, request.port)
                
                # Handle State Updates over replica nodes
                for rep_server in self.stubs:
                    try: 
                        reply = self.stubs[rep_server].NewUser_StateUpdate(request, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        self.logger.error(f"Exception: {rep_server} not alive on NewUser_StateUpdate")

                # Return existing players such that new joining players can recover the state players. 
                assignments = self.db.get('assignment')
                existing_players = []
                for username in assignments:
                    existing_players.append(quiplash_pb2.User(username=username,
                                                            ip_address=assignments[username]['ip'],
                                                            port=assignments[username]['port']))
                # add stub 
                self.create_stub(request.ip_address, request.port)

                # Persistence Add to db
                self._execute_log()
                print(f'New player joined {request.username}, {len(self._get_players())} players in the room')

                return quiplash_pb2.JoinGameReply(request_status=quiplash_pb2.SUCCESS,
                                                game_status=game_status,
                                                num_players=self.num_players,
                                                existing_players=existing_players)
        else:
            self.logger.error(f"ERROR: JoinGame request received on secondary node (primary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 


    def NewUser_StateUpdate(self, request, context):
        """
        Receives a state update with a new user that has 
        joined the game from the PRIMARY node.

        Running host:
        -------------
        Code in this function runs on SECONDARY node (called in PRIMARY).

        Parameters
        ----------
        request: User (quiplash.proto)
            User that has joined the game.
        
        Returns
        -------
        RequestReply:
            Confirms receipt of state update by the SECONDARY node.
        """
        if not self.is_primary:
            self.logger.info(f"STATE UPDT at {self.server_id}: NewUser_StateUpdate User({request.username})")
            
            # Add to log
            self._add_new_user_to_log(request.username, request.ip_address, request.port)
            self.create_stub(request.ip_address, request.port)
            # Execute pending log entries
            self._execute_log()
            return quiplash_pb2.RequestReply(reply='OK', request_status=quiplash_pb2.SUCCESS)
        
        else:
            self.logger.error(f"ERROR: NewUser State update request received on primary node (secondary only)")
            raise RuntimeError('Only secondary should receive this state update')

    def SendQuestions(self, request, context):
        """
        Receives a list of questions to answer from the PRIMARY node 
        (assigned questions to this user only).

        Running host:
        -------------
        Code in this function runs on SECONDARY node (called in PRIMARY).

        Parameters
        ----------
        request: QuestionList (quiplash.proto)
            List of questions that this user was assigned.
        
        Returns
        -------
        RequestReply:
            Confirms receipt of the question assignments by the SECONDARY node.
        """
        if not self.is_primary:
            self.logger.info(f"QUESTIONS RECV: Questions received ({len(request.question_list)}) at {self.address}")
            for question in request.question_list:
                question_prompt = self.db.dget("question_prompt", question.question_id)
                question_prompt['question_id'] = question.question_id

                # Add to local Client Storage
                self.unanswered_questions.append(question_prompt)

            return quiplash_pb2.RequestReply(reply = 'Success', 
                                            request_status=quiplash_pb2.SUCCESS)
        else:
            self.logger.error(f"ERROR: SendQuestions request received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 
    
    
    def QuestionAssignment_StateUpdate(self, request, context):
        """
        Receives a state update with a list of question assignments from the PRIMARY node.

        Running host:
        -------------
        Code in this function runs on PRIMARY node (called in SECONDARY).

        Parameters
        ----------
        request: QuestionList (quiplash.proto)
            List of questions with user for which they were assigned.
        
        Returns
        -------
        RequestReply:
            Confirms receipt of the question assignments by the SECONDARY node.
        """
        if not self.is_primary:
            self.logger.info(f"STATE UPDT at {self.server_id}: QuestionAssigment")

            if self.is_primary:
                self.logger.error(f"ERROR: STATE UPDT received at {self.server_id} when is_primary = {self.is_primary}")
                raise RuntimeError('Only secondary should run state updates')
            else :
                for question in request.question_list:
                    # Add Question to log
                    self._add_question_ass_to_log(question.destinatary.username,
                                                question.question_id)
                
                self._execute_log()

            return quiplash_pb2.RequestReply(reply = 'Success', 
                                            request_status=quiplash_pb2.SUCCESS)
        else:
            self.logger.error(f"ERROR: Question assignment State update request received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 

    
    
    def SendAnswer(self, request, context):
        """
        Request from secondary nodes to send an answer to a question to the primary node 

        Running host:
        -------------
        Code in this function runs on PRIMARY node (called in SECONDARY).

        Parameters
        ----------
        request: Answer (quiplash.proto)
            Answer to a question
        
        Returns
        -------
        RequestReply:
            Confirms receipt of the answer by the PRIMARY node.
        """
        if self.is_primary:
            if self.voting_started_prim: 
                # answer received after voting phase has started 
                self.logger.info(f"ANSWERS RECV: Received Answer from {request.respondent.username} after voting start, ignored")
                return quiplash_pb2.RequestReply(reply = 'Failed, voting has started', 
                                                request_status=quiplash_pb2.FAILED)
            else: 
                self.logger.info(f"ANSWERS RECV: Received Answer from {request.respondent.username}")

                # Add to log
                self._add_answer_to_log(request.respondent.username, request.question_id, request.answer_text)
                # Send State update to all replicas
                for rep_server in self.stubs:  
                    try: 
                        reply = self.stubs[rep_server].UserAnswer_StateUpdate(request, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        self.logger.error(f"Exception: {rep_server} not alive on UserAnswer_StateUpdate")

                # Persistence on DB
                self._execute_log()
                # Triggers voting phase if all answers have been received
                self._trigger_voting()

                return quiplash_pb2.RequestReply(reply = 'Success', 
                                                request_status=quiplash_pb2.SUCCESS)
        else:
            self.logger.error(f"ERROR: SendAnswer request received on secondary node (primary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 
        
    def UserAnswer_StateUpdate(self, request, context):
        """
        Receives a state update with an answer from the PRIMARY node.

        Running host:
        -------------
        Code in this function runs on SECONDARY node (called in PRIMARY).

        Parameters
        ----------
        request: Answer (quiplash.proto)
            Answer to a question
        
        Returns
        -------
        RequestReply:
            Confirms receipt of the state update by the SECONDARY node.
        """

        if not self.is_primary:
            self.logger.info(f"STATE UPDT at {self.server_id}: UserAnswer_StateUpdate")
            # Add to log
            self._add_answer_to_log(request.respondent.username, request.question_id, request.answer_text)
            # Make persistence on client
            self._execute_log()
            return quiplash_pb2.RequestReply(reply='OK', request_status=quiplash_pb2.SUCCESS)
        else:
            self.logger.error(f"ERROR: Vote State update request received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 
                                             
    def NotifyPlayers(self, request, context):
        """
        Notify players for synchronization purposes.

        Running host:
        -------------
        Code in this function runs on SECONDARY NODES (called in PRIMARY).

        Parameters
        ----------
        request: GameNotification (quiplash.proto)
            GameNotification of a given type (GAME_START, VOTING_START, SCORING_START). 

        Returns
        -------
        RequestReply:
            Confirms receipt of the notification by the SECONDARY node.
        """
        if not self.is_primary:
            request_name = quiplash_pb2.GameNotification.NotificationType.Name(request.type)
            self.logger.info(f"NOTIFICATION RECV: Received {request_name} Notification at {self.username}")
            if request.type == quiplash_pb2.GameNotification.GAME_START: 
                with self.game_started_cv:
                    self.game_started = True
                    self.game_started_cv.notify_all()  

            if request.type == quiplash_pb2.GameNotification.VOTING_START: 
                with self.voting_started_cv:
                    self.voting_started = True 
                    self.voting_started_cv.notify_all()
            
            if request.type == quiplash_pb2.GameNotification.SCORING_START: 
                with self.vote_tallying_started_cv:
                    self.vote_tallying_started = True 
                    self.vote_tallying_started_cv.notify_all()
            
            return quiplash_pb2.RequestReply(reply='Success', 
                                            request_status=quiplash_pb2.SUCCESS) 
        else:
            self.logger.error(f"ERROR: Synchronization notification received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 
    
    def SendAllAnswers(self, request, context):
        """
        Send all answers to secondary nodes (answers to all questions before for voting can begin)

        Running host:
        -------------
        Code in this function runs on SECONDARY NODES (called in PRIMARY).

        Parameters
        ----------
        request: AnswerList (quiplash.proto)
            List of Answers for questions.

        Returns
        -------
        RequestReply:
            Indicates Success or Failure of the request attempt.
            Confirms receipt of answers by the SECONDARY node.
        """
        if not self.is_primary:
            self.logger.info(f"ALL ANSWERS RECV: Received all anwers ({len(request.answer_list)}) at {self.username}")

            for answer in request.answer_list:
                self.logger.info(f"\t {answer.question_id}")

                self.answers_per_question[answer.question_id].append({
                    'user': answer.respondent.username, 
                    'answer': answer.answer_text})
                self.answers.append({'user': answer.respondent.username, 
                                    'answer': answer.answer_text, 
                                    'question_id': answer.question_id})
            
            return quiplash_pb2.RequestReply(reply='Success', 
                                            request_status=quiplash_pb2.SUCCESS)
        else: 
            self.logger.error(f"ERROR: ALL ANSWERS request received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED)
        
    def SendVote(self, request, context):
        """
        Receives an answer from a secondary node and manages replica state updates

        Running host:
        -------------
        Code in this function runs on PRIMARY NODE (called in SECONDARY NODES).

        Parameters
        ----------
        request: Vote (quiplash.proto)
            Vote for a given questions

        Returns
        -------
        RequestReply:
            Confirms receipt of vote by the PRIMARY node.
        """
        if self.is_primary:
            if self.vote_tallying_started_prim: 
                # vote received after vote tallying phase has started 
                self.logger.info(f"VOTE RECV: Received Vote after scoring started from {request.voter.username} to {request.votee.username} on question {request.question_id}")
                return quiplash_pb2.RequestReply(reply = 'Failed, scoring has started', 
                                                request_status=quiplash_pb2.FAILED)
            else: 
                self.logger.info(f"VOTE RECV: Vote received from {request.voter.username} to {request.votee.username} on question {request.question_id}")
                
                # Add to log
                self._add_vote_to_log(request.voter.username, request.question_id, request.votee.username)

                # Send State update to all replicas
                for rep_server in self.stubs:  
                    try: 
                        reply = self.stubs[rep_server].Vote_StateUpdate(request, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        self.logger.error(f"Exception: {rep_server} not alive on Vote_StateUpdate")

                self._execute_log() 
                # Triggers tallying phase if all votes have been received
                self._trigger_tallying()    
                return quiplash_pb2.RequestReply(reply='Success', 
                                                request_status=quiplash_pb2.SUCCESS) 
        else:
            self.logger.error(f"ERROR: Send Vote request received on secondary node (primary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 

    def Vote_StateUpdate(self, request, context):
        """
        Receives a state update with a vote from the PRIMARY node

        Running host:
        -------------
        Code in this function runs on SECONDARY NODES (called in PRIMARY NODES).

        Parameters
        ----------
        request: Vote (quiplash.proto)
            Vote for a given questions

        Returns
        -------
        RequestReply:
            Confirms receipt of state update by the PRIMARY node.
        """
        if not self.is_primary:
            self.logger.info(f"STATE UPDT at {self.server_id}: Vote_StateUpdate")
            # Add to log
            self._add_vote_to_log(request.voter.username, request.question_id, request.votee.username)
            # Persist changes in DB
            self._execute_log()

            return quiplash_pb2.RequestReply(reply='Success', 
                                            request_status=quiplash_pb2.SUCCESS) 
        else: 
            self.logger.error(f"ERROR: Vote State update request received on primary node (secondary only)")
            return quiplash_pb2.RequestReply(reply='Failure', 
                                             request_status=quiplash_pb2.FAILED) 


    def CheckLiveness(self, request, context):
        """
        Request sent periodically between servers to check for liveness.
        """
        return quiplash_pb2.LivenessResponse(status='OK')






    def _trigger_voting(self):
        """
        Check if all answers have been received for all questions
        and trigger voting if it is the case. 
        Voting is triggered by using a Conditional Variable which, when change to True,
        triggers the sending of a Notification to all SECONDARY NODES
        """

        pend_players = self._get_players_pending_ans()
        if len(pend_players) == 0:
            self.logger.info(f"\tAll anwers received")
            with self.voting_started_prim_cv:
                self.voting_started_prim = True
                self.voting_started_prim_cv.notify_all()
        else:
            self.logger.info(f"\tMissing answers from {pend_players}")

    def _trigger_tallying(self):
        """
        Trigger voting if all answers have been received
        """
        expected_votes, total_votes, pend_players = self._get_num_pending_votes()
        pend_votes = expected_votes - total_votes
        if pend_votes == 0:
            self.logger.info(f"\tAll votes received")
            with self.vote_tallying_started_prim_cv:
                self.vote_tallying_started_prim = True
                self.vote_tallying_started_prim_cv.notify_all()
        else:
            self.logger.info(f"\tMissing {pend_votes} out of {expected_votes} votes from {pend_players}")
            

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
        Checks if an answer has been received 
        for all assigned questions to all users
        """
        num_active_players = 0
        active_player_answers = 0
        players_missing_answers = []
        assignments = self.db.get('assignment')
        for player in assignments:
            address = f"{assignments[player]['ip']}:{assignments[player]['port']}"
            # check for liveness from stubs 
            if player != self.username and not self.replica_is_alive[address]:
                print("\n\n\n is this fucking it up? \n\n\n")
                continue

            active_player_answers += assignments[player]['answer_count']
            num_active_players += 1
            if assignments[player]['answer_count'] != QUESTIONS_PER_PLAYER:
                players_missing_answers.append(player)

        return players_missing_answers

    def _get_num_pending_votes(self):
        """
        Checks if a vote has been received 
        for all assigned answrers to all users
        """
        assignments = self.db.get('assignment')

        num_active_players = 0
        active_player_votes = 0
        players_missing_votes = []

        for player in assignments:
            address = f"{assignments[player]['ip']}:{assignments[player]['port']}"
            # check for liveness from stubs 
            if player != self.username and not self.replica_is_alive[address]:
                continue

            active_player_votes += assignments[player]['votes']
            num_active_players += 1
            if assignments[player]['votes'] != self.num_players:
                players_missing_votes.append(player)

        # number of unique questions is equal to the number of players (originally)
        expected_votes = num_active_players * self.num_players 

        # Compute difference 
        return expected_votes, active_player_votes, players_missing_votes
    
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

    def _get_votes_for_player(self, username): 
        return self.db.get("assignment")[username]

    # --------------------------------------------------------------------
    # ADD TO DB (Take from log and add to DB) 
    # --------------------------------------------------------------------
    def add_new_player(self, username, ip_address, port):
        """Add new player to the pickledb and update state"""
        # Add entry to db.
        self.db.dadd("assignment", (username, {"ip": ip_address, 
                                               "port": port, 
                                               "questions": {}, 
                                               "answer_count": 0,
                                               "votes": 0}))
        # Increase counter of total players.
        self.num_players += 1 
        self.address_to_user[f"{ip_address}:{port}"] = username

    def add_question_ass(self, username, question_id):
        """Add question assignment to the pickledb"""
        temp = self.db.get("assignment")
        temp[username]['questions'][question_id] = {"answer": "", "vote_count":0, "voters":[]}
        self.db.set("assignment", temp)

    def add_new_answer(self, username, question_id, answer_text):
        """Add answer to the pickledb"""
        temp = self.db.get("assignment")
        temp[username]['questions'][question_id]['answer'] = answer_text
        temp[username]['answer_count'] += 1 
        self.db.set("assignment", temp)

    def add_new_vote(self, voter, votee, question_id):
        """Add vote to the pickledb"""
        temp = self.db.get('assignment')
        # Add x
        if votee != EMPTY_ANS_DEFAULT:
            temp[votee]['questions'][question_id]['vote_count'] += 1
            temp[votee]['questions'][question_id]['voters'].append(voter)
        # Increase counter of how many times a user has voted
        temp[voter]['votes'] += 1
        self.db.set('assignment', temp)

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

    
    def tally_votes(self): 
        self.final_score = {}
        for player in self._get_players(): 
            player_votes = 0 
            questions = self._get_votes_for_player(player)["questions"]
            for question in questions:
                question_votes = questions[question]['vote_count']
                player_votes += question_votes
                if question_votes == self.num_players: 
                    player_votes += 1 # bonus point for unanimous vote 
            self.final_score[player] = player_votes * 100

    def display_votes(self):

        # Get the list of keys sorted by values
        players = sorted(self.final_score, key=self.final_score.get, reverse=True)

        # Get the list of values sorted
        scores = sorted(self.final_score.values(), reverse=True)

        # Calculate the width of each column
        max_player_length = max([len(player) for player in players])
        max_score_length = max([len(str(score)) for score in scores])
        column_width = max(max_player_length, max_score_length) + 2
        print("\n\n")
        # Print the table header
        print(f"\t\t\t   +{'-'*(column_width+2)}+{'-'*(column_width+2)}+")
        print(f"\t\t\t   | {'Player':^{column_width}} | {'Score':^{column_width}} |")

        # Print the table separator
        print(f"\t\t\t   +{'-'*(column_width+2)}+{'-'*(column_width+2)}+")

        # Print the rows
        for player, score in zip(players, scores):
            print(f"\t\t\t   | {player:{column_width}} | {score:{column_width}} |")

        # Print the table footer
        print(f"\t\t\t   +{'-'*(column_width+2)}+{'-'*(column_width+2)}+")


    def assign_questions(self):
        """
        Returns a dictionary of format player_address : [question_id, question_id,  ...]
        """
        if not self.is_primary: 
            raise RuntimeError("Only primary should run this function") 
        questions = self.db.get('question_prompt')
        if self.game_mode == 'all': 
            question_ids = list(questions.keys())
        elif self.game_mode in ['random', 'system']:
            question_ids = [question_id for question_id in questions if questions[question_id]['category'] == self.game_mode]
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
        logo = "  ______       __    __   __  .______    ___   .______    __           ___           _______. __    __     \n /  __  \     |  |  |  | |  | |   _  \  |__ \  |   _  \  |  |         /   \         /       ||  |  |  |    \n|  |  |  |    |  |  |  | |  | |  |_)  |    ) | |  |_)  | |  |        /  ^  \       |   (----`|  |__|  |    \n|  |  |  |    |  |  |  | |  | |   ___/    / /  |   ___/  |  |       /  /_\  \       \   \    |   __   |    \n|  `--'  '--. |  `--'  | |  | |  |       / /_  |  |      |  `----. /  _____  \  .----)   |   |  |  |  |    \n \_____\_____\ \______/  |__| | _|      |____| | _|      |_______|/__/     \__\ |_______/    |__|  |__|    "
        os.system('clear')
        print(logo)
        
        print("\n\n\n")
        host_mode = input("Start New Game or Join Existing (1 or 2): ")
        while host_mode not in ['1', '2']:
            print("\nOption must be `1` or `2`\n")
            host_mode = input("Start New Game or Join Existing (1 or 2): ")

        if host_mode == '1':
            # Primary Node
            self.setup_primary()
            # Prompt game mode 
            print("\n\n\n")
            print("Pick your game mode! This defines the types of questions you will see. \n")
            game_mode = input("All questions (1), random (2), systems theme (3): ")
            while game_mode not in ['1', '2', '3']:
                print("\nOption must be `1`, `2` or `3`.\n")
                game_mode = input("All questions (1), random (2), systems theme (3): ")
            modes = {'1': 'all', '2': 'random', '3': 'system'}
            self.game_mode = modes[game_mode]

        elif host_mode == '2':
            # Secondary Node
            game_host_address = input("Enter game code: ").strip().lower()
            while not check_valid_ip_format(game_host_address):
                game_host_address = input("Enter game code: ").strip().lower()
            
            ip, port = game_host_address.split(':')
            if self.create_stub(ip, port):
                self.primary_ip = ip
                self.primary_port = port
                self.primary_address = game_host_address
                self.replica_is_alive[game_host_address] = True
            else :
                print(f"Connection Failed: unable to connect to game in {game_host_address}")
                os._exit(1)

        #
        # JoinGame routine
        #  
        while True: 
            username = input("Enter username: ").strip().lower()
            if not username:
                print("Error: username cannot be empty")
            else:
                if self.is_primary:
                    self.username = username
                    self._add_new_user_to_log(self.username, self.ip, self.port)
                    self._execute_log()
                    break
                else:
                    user = quiplash_pb2.User(username=username, 
                                            ip_address=self.ip, 
                                            port=self.port)
                    reply = self.stubs[self.primary_address].JoinGame(user)
                    if reply.request_status == quiplash_pb2.FAILED:
                        if reply.game_status == quiplash_pb2.JoinGameReply.WAITING: 
                            print(f"Username {username} taken, try again")
                        elif reply.game_status == quiplash_pb2.JoinGameReply.STARTED:
                            print("here")
                            print("This game is already in progress! Start over and start new game or join other game.") 
                            os._exit(1)
                    else:
                        self.username = username
                        os.system('clear')
                        print(f"\n \n \t\t\t\t Welcome {self.username}! \n \t You successfully joined the game... hang around while others join")
                        self.server_id = reply.num_players

                        self._add_new_user_to_log(self.username, self.ip, self.port)

                        # Add all already existing players
                        for player in reply.existing_players:
                            self._add_new_user_to_log(player.username, player.ip_address, player.port)
                            self.create_stub(player.ip_address, player.port)
                        self._execute_log()
                        break
        
        #
        # QUESTION SETUP PHASE
        #
        if not self.is_primary: 
            # Wait until game phase starts
            with self.game_started_cv:
                while not self.game_started:
                    self.game_started_cv.wait()
        else:
            os.system('clear')
            print(f"\n \t\t\t\t Welcome, {self.username}! \t\t\t")
            print(f"\n\t\t Let others know the code to join your game: \n \t\t\t\t{self.address} \n")
            print("\n \t Once all players have joined the room, press <ENTER> to start game \n")
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
                    
                    # Add questions to local Client storage
                    if player_address == self.address:
                        question_prompt = self.db.dget("question_prompt", question_id)
                        question_prompt['question_id'] = question_id
                        self.unanswered_questions.append(question_prompt)

            # 
            # Send Assigned Questions to players
            # 
            for address, stub in self.stubs.items(): 
                player_questions = assigned_questions[address]
                grpc_question_list = self._get_questions_as_grpc_list(player_questions, self.username)
                reply = stub.SendQuestions(quiplash_pb2.QuestionList(question_list=grpc_question_list))

            # State Update for all Client Stubs with the assigned questions for all users
            all_question_list = []
            for address, question_ids in assigned_questions.items():
                username = self.address_to_user[address]
                all_question_list += self._get_questions_as_grpc_list(question_ids, username)
            grpc_all_question_list = quiplash_pb2.QuestionList(question_list=all_question_list)
            for ip, stub in self.stubs.items():
                if self.replica_is_alive[ip]:
                    state_update_reply = stub.QuestionAssignment_StateUpdate(grpc_all_question_list)

            self.game_started = True 
            # notifies other players game will begin 
            for ip, stub in self.stubs.items(): 
                if self.replica_is_alive[ip]:
                    notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.GAME_START)
                    reply = stub.NotifyPlayers(notification)


        #
        # ANSWERING PHASE
        #
        os.system('clear')
        print("\n \t\t\t Time to answer questions! \t\t\t")
        print(f"\n\t\t\tReady... Set.... QUIPLASH \t\t\n")
        print('\n\n\n')
        print(f"\t\tYou will be given 2 questions to answer in {TIME_PER_ANSWER}s each!\t\t")
        time.sleep(3)
        for idx, question in enumerate(self.unanswered_questions):
            print(f"\n\nQuestion {idx+1}/{len(self.unanswered_questions)}    Topic: {question['category']}")
            print(f"\n\t{question['question']}\n")
             
            answered = False
            try:
                # Take timed input using inputimeout() function
                answer_text = inputimeout(prompt='Your Answer: ', timeout=TIME_PER_ANSWER)
                if answer_text == "": 
                    answer_text = EMPTY_ANS_DEFAULT
                answered = True
            except TimeoutOccurred:
                if not answered:
                    answer_text = EMPTY_ANS_DEFAULT
                    print("You ran out of time! Moving to next question\n")
            
            if not self.is_primary:
                # Secondary nodes must SEND their answers to the primary node
                respondent = quiplash_pb2.User(username=self.username)
                grpc_answer = quiplash_pb2.Answer(respondent=respondent, 
                                                    answer_text=answer_text, 
                                                    question_id=question['question_id']) 
                reply = self.stubs[self.primary_address].SendAnswer(grpc_answer)
            
            else:
                # Primary node must UPDATE LOCAL STORAGE and send UPDATE to others
                # Add to log
                self._add_answer_to_log(self.username, question['question_id'], answer_text)
                # Send State update to all replicas
                for rep_server in self.stubs:  
                    try: 
                        respondent = quiplash_pb2.User(username=self.username)
                        grpc_answer = quiplash_pb2.Answer(respondent=respondent, 
                                                            answer_text=answer_text, 
                                                            question_id=question['question_id']) 
                        
                        reply = self.stubs[rep_server].UserAnswer_StateUpdate(grpc_answer, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        print(f"Exception: {rep_server} not alive on UserAnswer_StateUpdate")
                # Persistence on DB
                self._execute_log()
                # Triggers voting phase if all answers have been received
                self._trigger_voting()
                    
        #
        # VOTING SETUP PHASE
        #
        if not self.is_primary: 
            # Wait until voting phase starts (Queue is given by Notification from Server)
            with self.voting_started_cv:
                while not self.voting_started:
                    self.voting_started_cv.wait() 
               
        else:
            # Wait until voting started flag is set to True if all answers have been received or it timed out
            with self.voting_started_prim_cv:
                while not self.voting_started_prim:
                    val = self.voting_started_prim_cv.wait(timeout=TIME_PER_ANSWER * 2) # 2 questions per player 
                    self.voting_started_prim = True

            # 
            # Send Answers from players to players
            #            
            grpc_answers = self._get_answers_as_grpc()
            for address, stub in self.stubs.items():
                if self.replica_is_alive[address]:
                    print(f"Sending all ans {address}")
                    stub.SendAllAnswers(grpc_answers)


            assignments = self.db.get("assignment")
            for user in assignments:
                for question_id in assignments[user]['questions']:
                    answer = assignments[user]['questions'][question_id]['answer']
                    self.answers_per_question[question_id].append({
                        'user': user, 
                        'answer': answer})
                    self.answers.append({'user': user, 
                                        'answer': answer, 
                                        'question_id': question_id})

            #
            # Notifies other players voting phase begins
            # 
            for ip, stub in self.stubs.items():
                if self.replica_is_alive[ip]:
                    # print(f"Notify voting start all ans {ip}")
                    notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.VOTING_START)
                    reply = stub.NotifyPlayers(notification)
                    
        #
        # VOTING PHASE
        #
        os.system('clear')
        print('\t\t ___      ___ ________  _________  _______      ')
        print('\t\t|\\  \\    /  /|\\   __  \\|\\___   ___\\\\  ___ \\     ')
        print('\t\t\\ \\  \\  /  / | \\  \\|\\  \\|___ \\  \\_\\ \\   __/|    ')
        print('\t\t \\ \\  \\/  / / \\ \\  \\\\\\  \\   \\ \\  \\ \\ \\  \\_|/__  ')
        print('\t\t  \\ \\    / /   \\ \\  \\\\\\  \\   \\ \\  \\ \\ \\  \\_|\\ \\ ')
        print('\t\t   \\ \\__/ /     \\ \\_______\\   \\ \\__\\ \\ \\_______\\')
        print('\t\t    \\|__|/       \\|_______|    \\|__|  \\|_______|')
        time.sleep(2)

        print(f"\n\n\n \t\t\t Vote for the funniest answer! \t\t\n\n")
        
        for idx, question_id in enumerate(self.answers_per_question):
            question_info = self._get_question_data(question_id)
            print(f"\nPrompt: {question_info['question']}\n\n")
            print("Answers: \n")
            users_with_answer = []
            
            for ans_idx, answer in enumerate(self.answers_per_question[question_id]):
                print(f"({ans_idx + 1}) {answer['answer']}")
                users_with_answer.append(answer['user'])
            
            try:
                # Take timed input using inputimeout() function
                fav_answer = inputimeout(prompt='Your favorite answer is: ', timeout=TIME_PER_VOTE)                
                if fav_answer not in ['1', '2', '3']:
                    # player skipped vote for question 
                    print('Invalid vote was not registered. Moving to next question \n')
                    fav_answer = EMPTY_ANS_DEFAULT 
            except TimeoutOccurred:
                    fav_answer = EMPTY_ANS_DEFAULT 
                    print("\nYou ran out of time! Moving to next question\n")
            
            pref_user = users_with_answer[int(fav_answer)-1] if fav_answer != EMPTY_ANS_DEFAULT else EMPTY_ANS_DEFAULT
            
            if not self.is_primary:
                voter = quiplash_pb2.User(username=self.username)
                votee = quiplash_pb2.User(username=pref_user)
                grpc_vote = quiplash_pb2.Vote(voter=voter, 
                                                votee=votee,
                                                question_id=question_id)
                reply = self.stubs[self.primary_address].SendVote(grpc_vote)
            else: 
                # CHECK  
                self.logger.info(f"VOTE RECV: Vote received from {self.username} to {pref_user} on question {question_id}")
    
                # Add to log
                self._add_vote_to_log(self.username, question_id, pref_user)

                # send votes from primary to replicas
                for rep_server in self.stubs:  
                    try: 
                        voter = quiplash_pb2.User(username=self.username)
                        votee = quiplash_pb2.User(username=pref_user)
                        grpc_vote = quiplash_pb2.Vote(voter=voter, 
                                                        question_id=question_id,
                                                        votee=votee) 
                        
                        reply = self.stubs[rep_server].Vote_StateUpdate(grpc_vote, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        print(f"Exception: {rep_server} not alive on Vote_StateUpdate")

                # Persistance on db 
                self._execute_log()     
                # Triggers voting tallying phase if all votes have been received (or timed out)
                self._trigger_tallying()

        #
        # TALLYING VOTES PHASE  
        # 
        os.system('clear') 
        print("\t ________  ________  ________  ________  _______   ________      ")
        print("\t|\\   ____\\|\\   ____\\|\\   __  \\|\\   __  \\|\\  ___ \\ |\\   ____\\     ")
        print("\t\\ \\  \\___|\\ \\  \\___|\\ \\  \\|\\  \\ \\  \\|\\  \\ \\   __/|\\ \\  \\___|_    ")
        print("\t \\ \\_____  \\ \\  \\    \\ \\  \\\\\\  \\ \\   _  _\\ \\  \\_|/_\\ \\_____  \\   ")
        print("\t  \\|____|\\  \\ \\  \\____\\ \\  \\\\\\  \\ \\  \\\\  \\\\ \\  \\_|\\ \\|____|\\  \\  ")
        print("\t    ____\\_\\  \\ \\_______\\ \\_______\\ \\__\\\\ _\\\\ \\_______\\____\\_\\  \\ ")
        print("\t   |\\_________\\|_______|\\|_______|\\|__|\\|__|\\|_______|\\_________\\")
        print("\t   \\|_________|                                      \\|_________|")
        time.sleep(2) 
        #
        # VOTING TALLYING SETUP PHASE
        #
        if not self.is_primary: 
            # Wait until voting phase ends (Queue is given by Notification from Server)
            with self.vote_tallying_started_cv:
                while not self.vote_tallying_started:
                    self.vote_tallying_started_cv.wait() 
               
        else:
            # Wait until voting started flag is set to True if all answers have been received or it timed out
            with self.vote_tallying_started_prim_cv:
                while not self.vote_tallying_started_prim:
                    val = self.vote_tallying_started_prim_cv.wait(timeout=TIME_PER_VOTE * self.num_players) # number of unique questions is defined by number of players
                    self.vote_tallying_started_prim = True
            
            #
            # Notifies other players voting phase begins
            # 
            for ip, stub in self.stubs.items():
                notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.SCORING_START)
                reply = stub.NotifyPlayers(notification)

        self.tally_votes()
        self.display_votes() 


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

    # Start the liveness check thread with the existing gRPC channel and stub
    liveness_thread = threading.Thread(target=liveness_check_thread, args=(quiplash_servicer,))
    liveness_thread.start()

    server.wait_for_termination()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    servers = [1, 2, 3, 4, 5, 6, 7, 8]
    parser.add_argument("-P", "--port", help="Port of where server will be running", type=str, default=os.environ['QUIPLASH_SERVER_PORT'])
    args = parser.parse_args()
    serve(args.port) 
