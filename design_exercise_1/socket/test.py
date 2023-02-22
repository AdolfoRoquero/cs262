import unittest
from utils import * 
from client import *
import random 
import string 
from protocol import *
import time
import os

class TestLoginSignUp(unittest.TestCase):
    host = os.environ['CHAT_APP_SERVER_HOST']
    port = os.environ['CHAT_APP_SERVER_PORT']
    sleep_time = 2
    fake_users = ['user_to_login','user_to_delete', 'A_user', 'B_user']

    @classmethod
    def setUpClass(cls):
        print("\n\nSet Up TestLoginSignUp")
        # Setup fake usernames
        for username in cls.fake_users: 
            print(f"\tAdd {username}")
            setup_client = Client(host=cls.host, 
                                  port=cls.port)
            setup_client.setup()
            result = setup_client.sign_up(username)
            time.sleep(cls.sleep_time)
            signup_reply = setup_client.receive_message()
            assert(signup_reply['metadata']['message_type'] == SRV_SIGNUP), f"{username} with status {signup_reply['metadata']['message_type']}"
            setup_client.close()

    @classmethod
    def tearDownClass(cls):
        print("\n\nTear Down TestLoginSignUp")
        # Setup fake usernames
        for username in cls.fake_users:
            print(f"\tRemove {username}")
            del_client = Client(host=cls.host, 
                                port=cls.port)
            del_client.setup()
            login_result = del_client.login(username)
            time.sleep(cls.sleep_time)
            login_reply = del_client.receive_message()
            assert (login_reply['metadata']['message_type'] == SRV_LOGIN), f"{username} with status {login_reply['metadata']['message_type']}"
            del_result = del_client.del_user()
            time.sleep(cls.sleep_time)
            signup_reply = del_client.receive_message()
            assert(signup_reply['metadata']['message_type'] == SRV_DEL_USER)
            del_client.close()
    
    def setUp(self):
        self.client = Client(host=self.host, port=self.port)
        self.client.setup()

    def tearDown(self):
        self.client.close()

    def test_valid_login(self):
        """
        Test that login with a valid existing username is successful.
        """
        result = self.client.login('user_to_login')
        time.sleep(self.sleep_time)
        login_reply = self.client.receive_message()
        # asserts login on the server side succeded 
        self.assertEqual(login_reply['metadata']['message_type'], SRV_LOGIN)

    
    def test_invalid_login(self): 
        """
        Test that login with a random username (not registered) is not successful.
        """
        letters = string.ascii_lowercase
        random_username = ''.join(random.choice(letters) for i in range(10))
        result = self.client.login(random_username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(random_username))
        time.sleep(self.sleep_time)
        login_reply = self.client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(login_reply['metadata']['message_type'], SRV_MSG_FAILURE)
        
    
    def test_valid_signup(self):
        """
        Test that creating an account with a new user works. 
        """
        letters = string.ascii_lowercase
        username = 'test_signup'
        self.fake_users.append(username)
        result = self.client.sign_up(username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(username))
        time.sleep(self.sleep_time)
        signup_reply = self.client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(signup_reply['metadata']['message_type'], SRV_SIGNUP)

    def test_invalid_signup(self):
        """
        Test that signing up with an already existing account username fails.
        """
        # Username 'B_user' is already taken
        username = 'B_user'
        result = self.client.sign_up(username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(username))
        time.sleep(self.sleep_time)
        signup_reply = self.client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(signup_reply['metadata']['message_type'], SRV_MSG_FAILURE)
    
    def test_del_user(self):
        """
        Test that deleting one's own username works.
        """
        result = self.client.login('user_to_delete')
        time.sleep(self.sleep_time)
        login_reply = self.client.receive_message()
        # asserts login on the server side succeded 
        self.assertEqual(login_reply['metadata']['message_type'], SRV_LOGIN)

        # Delete user
        result = self.client.del_user()
        time.sleep(self.sleep_time)
        del_user_reply = self.client.receive_message()
        self.assertEqual(del_user_reply['metadata']['message_type'], SRV_DEL_USER)
        self.fake_users.remove('user_to_delete')


class TestClientFunctions(unittest.TestCase):
    host = os.environ['CHAT_APP_SERVER_HOST']
    port = os.environ['CHAT_APP_SERVER_PORT']
    sleep_time = 2
    fake_users = ['A_user', 'B_user', 'C_user']
      
    @classmethod
    def setUpClass(cls):
        print("\n\nSet Up TestClientFunctions")

        # Setup fake usernames
        for username in cls.fake_users: 
            print(f"\tAdd {username}")
            setup_client = Client(host=cls.host, 
                                  port=cls.port)
            setup_client.setup()
            result = setup_client.sign_up(username)
            time.sleep(cls.sleep_time)
            signup_reply = setup_client.receive_message()
            assert(signup_reply['metadata']['message_type'] == SRV_SIGNUP), f"{username} with status {signup_reply['metadata']['message_type']}"
            setup_client.close()

    @classmethod
    def tearDownClass(cls):
        print("\n\nTearDownClass")
        # Setup fake usernames
        for username in cls.fake_users:
            print(f"\tRemove {username}")
            del_client = Client(host=cls.host, 
                                port=cls.port)
            del_client.setup()
            login_result = del_client.login(username)
            time.sleep(cls.sleep_time)
            login_reply = del_client.receive_message()
            assert (login_reply['metadata']['message_type'] == SRV_LOGIN), f"{username} with status {login_reply['metadata']['message_type']}"
            del_result = del_client.del_user()
            time.sleep(cls.sleep_time)
            signup_reply = del_client.receive_message()
            assert(signup_reply['metadata']['message_type'] == SRV_DEL_USER)
            del_client.close()
        
    def setUp(self):
        self.client = Client(host=self.host, port=self.port)
        self.client.setup()
        result = self.client.login('ROOT')
        time.sleep(self.sleep_time)
        login_reply = self.client.receive_message()
        self.assertEqual(login_reply['metadata']['message_type'], SRV_LOGIN)

    def tearDown(self):
        self.client.close()

    def test_listall_nofilter(self): 
        result = self.client.listall('*')
        time.sleep(self.sleep_time)
        listall_reply = self.client.receive_message()

        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)
        # asserts filtering by usename is correct 
        self.assertEqual(['ROOT'] + self.fake_users , listall_reply['message_content'])
        
    def test_listall_startswith(self): 
        result = self.client.listall('B*')
        time.sleep(self.sleep_time)
        listall_reply = self.client.receive_message()
        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)
        # asserts filtering by wildcard filter is correct 
        for username in listall_reply['message_content']: 
            self.assertRegex(username, 'B*')
    
    def test_listall_endswith(self):
        result = self.client.listall('*_user')
        time.sleep(self.sleep_time)
        listall_reply = self.client.receive_message()

        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)

        # asserts filtering by wildcard filter is correct 
        for username in listall_reply['message_content']: 
            self.assertRegex(username, '.*_user')
        self.assertEqual(listall_reply['message_content'], ['A_user', 'B_user', 'C_user'])

    

        
    

    
if __name__ == '__main__':
    unittest.main()