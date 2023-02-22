import unittest 
import string 
import random 
import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 


# HOST = "192.168.0.114"
# PORT = "50051"

class TestClient(unittest.TestCase):
    host = os.environ['CHAT_APP_SERVER_HOST']
    port = os.environ['CHAT_APP_SERVER_PORT']
    sleep_time = 3
    fake_users = ['A_user', 'B_user', 'C_user']

    @classmethod
    def setUpClass(cls):
        print("\n\nSetUpClass")

        # Setup fake usernames
        with grpc.insecure_channel(f'{cls.host}:{cls.port}') as channel:
            for username in cls.fake_users: 
                stub = chat_app_pb2_grpc.ChatAppStub(channel)
                user = chat_app_pb2.User(username = username)
                reply = stub.SignUp(user)
                assert(1 == reply.request_status)

    @classmethod
    def tearDownClass(cls):
        # Setup fake usernames
        with grpc.insecure_channel(f'{cls.host}:{cls.port}') as channel:
            for username in cls.fake_users:
                stub = chat_app_pb2_grpc.ChatAppStub(channel)
                user = chat_app_pb2.User(username = username)
                reply = stub.Login(user)
                assert(1 == reply.request_status)
                reply = stub.DeleteUser(user)
                assert(1 == reply.request_status)

    def setUp(self):
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
                stub = chat_app_pb2_grpc.ChatAppStub(channel)
                user = chat_app_pb2.User(username = 'root')
                reply = stub.Login(user)
                self.assertEqual(1, reply.request_status)
            

    def test_invalid_login(self): 
        """
        Test that logging in with a random username (not registered) is not successful.
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
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
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            for username in self.fake_users:
                stub = chat_app_pb2_grpc.ChatAppStub(channel)
                user = chat_app_pb2.User(username = username)
                reply = stub.Login(user)
                self.assertEqual(1, reply.request_status)

    def test_signup(self): 
        """
        Test that signing up with a random username (not registered) is successfull 
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            letters = string.ascii_lowercase
            random_username = ''.join(random.choice(letters) for i in range(10))
            user = chat_app_pb2.User(username = random_username)
            reply = stub.SignUp(user)
            self.assertEqual(1, reply.request_status)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            self.assertIn(random_username, [user.username for user in reply.users])
            

    def test_invalid_signup(self): 
        """
        Test that signing up with a registered username is not successful 
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user = chat_app_pb2.User(username = 'root')
            reply = stub.SignUp(user)
            self.assertEqual(0, reply.request_status)

    def test_listall(self): 
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            self.assertGreaterEqual(len(reply.users), 3)
    
    def test_listall_filter(self): 
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*user')
            reply = stub.ListAll(username_filter) 
            for user in reply.users: 
                print(user.username)
                self.assertRegex(user.username, '.*_user')
            self.assertEqual(len(reply.users), 3)


    def test_del_user(self): 
        """
        Test that deleting a user is successful 
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user = chat_app_pb2.User(username = 'USER_TO_DELETE')
            reply = stub.SignUp(user)
            self.assertEqual(1, reply.request_status)
            reply = stub.DeleteUser(user)
            self.assertEqual(1, reply.request_status)
            username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
            reply = stub.ListAll(username_filter) 
            self.assertNotIn(user.username, [user.username for user in reply.users])

    def test_send_message(self): 
        """
        Test that a message can be sent from one user to another 
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            user1 = chat_app_pb2.User(username = self.fake_users[0])
            user2 = chat_app_pb2.User(username = self.fake_users[1])
            user3 = chat_app_pb2.User(username = self.fake_users[2])
            reply = stub.Login(user1)
            self.assertEqual(1, reply.request_status)
            
            msg_datetime = Timestamp()
            msg_datetime.GetCurrentTime()
            msg_text = 'Hi test users!'
            chat_message = chat_app_pb2.ChatMessage(
                        sender = user1, destinataries = chat_app_pb2.UserList(users=[user2, user3]), 
                        text = msg_text, date = msg_datetime)
            reply = stub.SendMessage(chat_message)
            self.assertEqual(1, reply.request_status)

            for user in [user2, user3]: 
                user_reply = stub.ReceiveMessage(user)  
                for msg_received in user_reply: 
                    self.assertEqual(msg_text, msg_received.text) 

    def test_deliver_pending_messages(self): 
        """
        Test that a message can be sent from one user to another 
        """
        with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
            stub = chat_app_pb2_grpc.ChatAppStub(channel)
            username = 'root'
            user = chat_app_pb2.User(username = username)
            reply = stub.Login(user)
            self.assertEqual(1, reply.request_status)
            msg_datetime = Timestamp()
            msg_datetime.GetCurrentTime()
            msg_text = 'Testing delayed message delivery!'
            user2 = chat_app_pb2.User(username = self.fake_users[1])
            chat_message = chat_app_pb2.ChatMessage(
                        sender = user, destinataries = chat_app_pb2.UserList(users=[user2]), 
                        text = msg_text, date = msg_datetime)
            reply = stub.SendMessage(chat_message)
            self.assertEqual(1, reply.request_status)
            reply = stub.Login(user2)
            self.assertEqual(1, reply.request_status)
            reply = stub.ReceiveMessage(user2) 
            for msg_received in reply: 
                    self.assertEqual(msg_text, msg_received.text) 

if __name__ == '__main__':
    unittest.main()