import unittest 
import string 
import random 
import quiplash_pb2
import quiplash_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 
from utils import check_valid_ip_format
from node import QuiplashServicer
import socket
from concurrent import futures


def test_valid_ip_checker():
    """Test util function for valid IP checking"""
    # Test that checker accepts valid entries
    assert check_valid_ip_format("127.30.239.8:89"), "Should be accepted"
    assert check_valid_ip_format("127.200.239.100:8009"), "Should be accepted"
    assert check_valid_ip_format("1.1.1.1:1"), "Should be accepted"
    assert check_valid_ip_format("10.10.10.10:10"), "Should be accepted"

    # Test that checker rejects invalid entries
    assert not check_valid_ip_format(""), "Should have been rejected"
    assert not check_valid_ip_format("abcdefghigk"), "Should have been rejected"
    assert not check_valid_ip_format("lsdfsdf:fghigk"), "Should have been rejected"
    assert not check_valid_ip_format("500.500.500.500:20000"), "Should have been rejected"
    assert not check_valid_ip_format("a.b.c.d:e"), "Should have been rejected"


class TestClass():
    def setup(self):
        self.IP = socket.gethostbyname(socket.gethostname())
        self.PORT = 6000
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.primary_node = QuiplashServicer(self.IP, self.PORT)
        quiplash_pb2_grpc.add_QuiplashServicer_to_server(self.primary_node, self.server)
        self.server.add_insecure_port(f'{self.IP}:{self.PORT}')
        self.server.start()

        self.primary_node.setup_primary()

        # Stub for random requests
        self.stub = quiplash_pb2_grpc.QuiplashStub(grpc.insecure_channel(f"{self.IP}:{self.PORT}"))

        # Default user 1
        self.username1 = "TestUser1"
        self.port1 = "60100"
        self.address1 = f"{self.IP}:{self.port1}"
        self.stub1 = quiplash_pb2_grpc.QuiplashStub(grpc.insecure_channel(f"{self.IP}:{self.PORT}"))
        self.user1 = quiplash_pb2.User(username=self.username1, 
                                ip_address=self.IP, 
                                port=self.port1)

        # Default user 2
        self.username2 = "TestUser2"
        self.port2 = "60200"
        self.address2 = f"{self.IP}:{self.port2}"
        self.stub2 = quiplash_pb2_grpc.QuiplashStub(grpc.insecure_channel(f"{self.IP}:{self.PORT}"))
        self.user2 = quiplash_pb2.User(username=self.username2, 
                                ip_address=self.IP, 
                                port=self.port2)
        
        
        reply = self.stub1.JoinGame(self.user1)
        assert reply.request_status == quiplash_pb2.SUCCESS

        reply = self.stub2.JoinGame(self.user2)
        assert reply.request_status == quiplash_pb2.SUCCESS

    def cleanup(self):
        self.server.stop(grace=0)
        del self.server
        del self.primary_node
        del self.stub2
        del self.stub1


    def test_JoinGame(self):
        self.setup()

        # Test adding a valid user
        validusername = "ValidUsername"
        validuser = quiplash_pb2.User(username=validusername, 
                                      ip_address=self.IP, 
                                      port="70000")
        reply = self.stub.JoinGame(validuser)
        assert reply.request_status == quiplash_pb2.SUCCESS
        

        # Test adding an invalid user
        usernametaken = "TestUser1"
        takenuser = quiplash_pb2.User(username=usernametaken, 
                                      ip_address=self.IP, 
                                      port=self.port1)
        reply = self.stub.JoinGame(takenuser)
        assert reply.request_status == quiplash_pb2.FAILED

        # Test adding a user after game has started
        self.primary_node.game_started = True

        username_already_started = "GameAlreadyStarted"
        user_already_started = quiplash_pb2.User(username=username_already_started, 
                                      ip_address=self.IP, 
                                      port="80000")
        reply = self.stub.JoinGame(user_already_started)
        assert reply.request_status == quiplash_pb2.FAILED
        assert reply.game_status == quiplash_pb2.JoinGameReply.STARTED

        self.cleanup()

    def test_QuestionAssigner(self):
        self.setup()

        # Test assignment of questions for the 2 default users
        self.primary_node.game_mode = 'all'
        assigned_questions = self.primary_node.assign_questions()
        assert self.address1 in assigned_questions
        assert self.address2 in assigned_questions
        assert len(assigned_questions[self.address1]) == 2
        assert len(assigned_questions[self.address2]) == 2

        # Test adding a 3rd valid user
        validusername = "ValidUsername"
        port = "70000"
        address = f"{self.IP}:{port}"
        validuser = quiplash_pb2.User(username=validusername, 
                                      ip_address=self.IP, 
                                      port=port)
        reply = self.stub.JoinGame(validuser)
        assert reply.request_status == quiplash_pb2.SUCCESS


        # Test assignment of questions for the 3 users
        self.primary_node.game_mode = 'all'
        assigned_questions = self.primary_node.assign_questions()
        assert self.address1 in assigned_questions
        assert self.address2 in assigned_questions
        assert address in assigned_questions
        assert len(assigned_questions[self.address1]) == 2
        assert len(assigned_questions[self.address2]) == 2
        assert len(assigned_questions[address]) == 2
        self.cleanup()





    def test_AssignQuestions(self):
        self.setup()

        self.primary_node.game_started = True

        player_questions = assigned_questions[address]
        grpc_question_list = self._get_questions_as_grpc_list(player_questions, self.username)
        destinatary = quiplash_pb2.User(username=username)
        question_list = [] 
        for question_id in question_ids:
            question_dict = self.db.dget('question_prompt', question_id)
            grpc_question = quiplash_pb2.Question(question_id=question_id, 
                                                  question_text=question_dict['question'],
                                                  topic=question_dict['category'],
                                                  destinatary=destinatary)
            question_list.append(grpc_question)
        reply = self.stub1.SendQuestions(quiplash_pb2.QuestionList(question_list=grpc_question_list))

        

        username_already_started = "GameAlreadyStarted"
        user_already_started = quiplash_pb2.User(username=username_already_started, 
                                      ip_address=self.IP, 
                                      port="80000")
        reply = self.stub.JoinGame(user_already_started)
        assert reply.request_status == quiplash_pb2.FAILED
        assert reply.game_status == quiplash_pb2.JoinGameReply.STARTED

        self.cleanup()
    
    def run_tests(self):
        self.test_JoinGame()
        self.test_QuestionAssigner()


if __name__ == '__main__':
    tests = TestClass()
    tests.run_tests()
    test_valid_ip_checker()
