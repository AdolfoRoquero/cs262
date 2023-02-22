import unittest 
import string 
import random 
import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc


HOST = "192.168.0.114"
PORT = "50051"

class TestClient(unittest.TestCase):
    
    def test_invalid_login(self): 
        """
        Test that logging in with a random username (not registered) is not successfull 
        """
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            letters = string.ascii_lowercase
            random_username = ''.join(random.choice(letters) for i in range(10))
            user = chat_app_pb2.User(username = random_username)
            reply = stub.Login(user)
            self.assertEqual(0, reply.request_status)
    
    def test_login(self): 
        """
        Test that logging in with a registered username is successfull 
        """
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user = chat_app_pb2.User(username = 'test123')
            reply = stub.Login(user)
            self.assertEqual(1, reply.request_status)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            print(reply)

    def test_signup(self): 
        """
        Test that signing up with a random username (not registered) is successfull 
        """
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            letters = string.ascii_lowercase
            random_username = ''.join(random.choice(letters) for i in range(10))
            user = chat_app_pb2.User(username = random_username)
            reply = stub.SignUp(user)
            self.assertEqual(1, reply.request_status)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            print('added new user', reply)

    def test_invalid_signup(self): 
        """
        Test that signing up with a registered username is not successful 
        """
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user = chat_app_pb2.User(username = 'test123')
            reply = stub.SignUp(user)
            self.assertEqual(0, reply.request_status)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            print(reply)

    def test_listall(self): 
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            #TODO  FIX THIS ONE 
            # self.assertGreaterEqual(len(reply.users), 2)
    
    def test_listall_filter(self): 
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = 't*')
            reply = stub.ListAll(username_filter) 
            for user in reply.users: 
                self.assertRegexpMatches(user.username, 't*')


    def test_del_user(self): 
        """
        Test that deleting a user is successful 
        """
        with grpc.insecure_channel(f'{HOST}:{PORT}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user = chat_app_pb2.User(username = 'test123')
            reply = stub.DeleteUser(user)
            self.assertEqual(1, reply.request_status)

    
if __name__ == '__main__':
    unittest.main()