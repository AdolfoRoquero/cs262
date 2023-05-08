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


def setup():
    IP = socket.gethostbyname(socket.gethostname())
    PORT = 6000
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    primary_node = QuiplashServicer(IP, PORT)
    quiplash_pb2_grpc.add_QuiplashServicer_to_server(primary_node, server)
    server.add_insecure_port(f'{IP}:{PORT}')
    server.start()

    primary_node = 



    address1 = f"{IP}:{60100}"
    stub1 = quiplash_pb2_grpc.QuiplashStub(grpc.insecure_channel(address1))

    address2 = f"{IP}:{60200}"
    stub2 = quiplash_pb2_grpc.QuiplashStub(grpc.insecure_channel(address2))


    

    server.stop(grace=0)
    


    


# class TestClient(unittest.TestCase):
#     host = os.environ['CHAT_APP_SERVER_HOST']
#     port = os.environ['CHAT_APP_SERVER_PORT']
#     sleep_time = 3
#     fake_users = ['A_user', 'B_user', 'C_user']

#     @classmethod
#     def setUpClass(cls):
#         # Setup fake usernames
#         with grpc.insecure_channel(f'{cls.host}:{cls.port}') as channel:
#             for username in cls.fake_users: 
#                 stub = chat_app_pb2_grpc.ChatAppStub(channel)
#                 user = chat_app_pb2.User(username = username)
#                 reply = stub.SignUp(user)
#                 assert(1 == reply.request_status)

#     @classmethod
#     def tearDownClass(cls):
#         # Setup fake usernames
#         with grpc.insecure_channel(f'{cls.host}:{cls.port}') as channel:
#             for username in cls.fake_users:
#                 stub = chat_app_pb2_grpc.ChatAppStub(channel)
#                 user = chat_app_pb2.User(username = username)
#                 reply = stub.Login(user)
#                 assert(1 == reply.request_status)
#                 reply = stub.DeleteUser(user)
#                 assert(1 == reply.request_status)

#     def setUp(self):
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#                 stub = chat_app_pb2_grpc.ChatAppStub(channel)
#                 user = chat_app_pb2.User(username = 'root')
#                 reply = stub.Login(user)
#                 self.assertEqual(1, reply.request_status)
            

#     def test_invalid_login(self): 
#         """
#         Test that logging in with a random username (not registered) is not successful.
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             letters = string.ascii_lowercase
#             random_username = ''.join(random.choice(letters) for i in range(10))
#             user = chat_app_pb2.User(username = random_username)
#             reply = stub.Login(user)
#             self.assertEqual(0, reply.request_status)
    
#     def test_login(self): 
#         """
#         Test that logging in with a registered username is successfull 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             for username in self.fake_users:
#                 stub = chat_app_pb2_grpc.ChatAppStub(channel)
#                 user = chat_app_pb2.User(username = username)
#                 reply = stub.Login(user)
#                 self.assertEqual(1, reply.request_status)

#     def test_signup(self): 
#         """
#         Test that signing up with a random username (not registered) is successfull 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             letters = string.ascii_lowercase
#             random_username = ''.join(random.choice(letters) for i in range(10))
#             user = chat_app_pb2.User(username = random_username)
#             reply = stub.SignUp(user)
#             self.assertEqual(1, reply.request_status)
#             username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
#             reply = stub.ListAll(username_filter) 
#             self.assertIn(random_username, [user.username for user in reply.users])
            

#     def test_invalid_signup(self): 
#         """
#         Test that signing up with a registered username is not successful 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             user = chat_app_pb2.User(username = 'root')
#             reply = stub.SignUp(user)
#             self.assertEqual(0, reply.request_status)

#     def test_listall(self): 
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
#             reply = stub.ListAll(username_filter) 
#             self.assertGreaterEqual(len(reply.users), 3)
    
#     def test_listall_filter(self): 
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             username_filter = chat_app_pb2.ListAllRequest(username_filter = '*user')
#             reply = stub.ListAll(username_filter) 
#             for user in reply.users: 
#                 self.assertRegex(user.username, '.*_user')
#             self.assertEqual(len(reply.users), 3)


#     def test_del_user(self): 
#         """
#         Test that deleting a user is successful 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             user = chat_app_pb2.User(username = 'USER_TO_DELETE')
#             reply = stub.SignUp(user)
#             self.assertEqual(1, reply.request_status)
#             reply = stub.DeleteUser(user)
#             self.assertEqual(1, reply.request_status)
#             username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
#             reply = stub.ListAll(username_filter) 
#             self.assertNotIn(user.username, [user.username for user in reply.users])

#     def test_send_message(self): 
#         """
#         Test that a message can be sent from one user to another 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             user1 = chat_app_pb2.User(username = self.fake_users[0])
#             user2 = chat_app_pb2.User(username = self.fake_users[1])
#             user3 = chat_app_pb2.User(username = self.fake_users[2])
#             reply = stub.Login(user1)
#             self.assertEqual(1, reply.request_status)
            
#             msg_datetime = Timestamp()
#             msg_datetime.GetCurrentTime()
#             msg_text = 'Hi test users!'
#             chat_message = chat_app_pb2.ChatMessage(
#                         sender = user1, destinataries = chat_app_pb2.UserList(users=[user2, user3]), 
#                         text = msg_text, date = msg_datetime)
#             reply = stub.SendMessage(chat_message)
#             self.assertEqual(1, reply.request_status)

#             for user in [user2, user3]: 
#                 user_reply = stub.ReceiveMessage(user)  
#                 for msg_received in user_reply: 
#                     self.assertEqual(msg_text, msg_received.text) 

#     def test_deliver_pending_messages(self): 
#         """
#         Test that a message can be sent from one user to another 
#         """
#         with grpc.insecure_channel(f'{self.host}:{self.port}') as channel:
#             stub = chat_app_pb2_grpc.ChatAppStub(channel)
#             username = 'root'
#             user = chat_app_pb2.User(username = username)
#             reply = stub.Login(user)
#             self.assertEqual(1, reply.request_status)
#             msg_datetime = Timestamp()
#             msg_datetime.GetCurrentTime()
#             msg_text = 'Testing delayed message delivery!'
#             user2 = chat_app_pb2.User(username = self.fake_users[1])
#             chat_message = chat_app_pb2.ChatMessage(
#                         sender = user, destinataries = chat_app_pb2.UserList(users=[user2]), 
#                         text = msg_text, date = msg_datetime)
#             reply = stub.SendMessage(chat_message)
#             self.assertEqual(1, reply.request_status)
#             reply = stub.Login(user2)
#             self.assertEqual(1, reply.request_status)
#             reply = stub.ReceiveMessage(user2) 
#             for msg_received in reply: 
#                     self.assertEqual(msg_text, msg_received.text) 

if __name__ == '__main__':

    #test_valid_ip_checker()
    setup()