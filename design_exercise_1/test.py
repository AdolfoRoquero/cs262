import unittest
from utils import * 
from client import *
import random 
import string 
from protocol import *
import time


HOST = "192.168.0.114"

class TestLoginSignUp(unittest.TestCase):
    
    def test_invalid_login(self): 
        """
        Test that logging in with a random username (not registered) is not successfull 
        """
        client = Client(host=HOST)
        client.setup()
        letters = string.ascii_lowercase
        random_username = ''.join(random.choice(letters) for i in range(10))
        result = client.login(random_username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(random_username))
        time.sleep(1)
        login_reply = client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(login_reply['metadata']['message_type'], SRV_MSG_FAILURE)
        client.close()
    
    def test_signup(self):
        """
        Test that creating an account with a new user works 
        """
        client = Client(host=HOST)
        client.setup()
        letters = string.ascii_lowercase
        username = 'test123'
        result = client.sign_up(username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(username))
        time.sleep(1)
        signup_reply = client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(signup_reply['metadata']['message_type'], SRV_SIGNUP)
        client.close()

    def test_signup_failure(self):

        client = Client(host=HOST)
        client.setup()
        username = 'test123'
        result = client.sign_up(username)
        # asserts correct message was sent to server 
        self.assertEqual(result, 34 + len(username))
        time.sleep(1)
        signup_reply = client.receive_message()
        # asserts login on the server side failed 
        self.assertEqual(signup_reply['metadata']['message_type'], SRV_MSG_FAILURE)
        client.close()
   

class TestClientFunctions(unittest.TestCase):
    client = Client(host=HOST)
    client.setup()
    username = 'test123'
    result = client.login(username)
    time.sleep(1)
    login_reply = client.receive_message()
    time.sleep(1)

    def test_listall_nofilter(self): 
        result = self.client.listall(self.username, '*')
        time.sleep(1)
        listall_reply = self.client.receive_message()
        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)
        # asserts filtering by usename is correct 
        self.assertIn(self.username, listall_reply['message_content'])
        time.sleep(1)
        
    def test_listall_startswith(self): 
        result = self.client.listall(self.username, 't*')
        time.sleep(1)
        listall_reply = self.client.receive_message()
        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)
        # asserts filtering by wildcard filter is correct 
        for username in listall_reply['message_content']: 
            self.assertRegexpMatches(username, 't*')
    
    def test_listall_endswith(self):
        result = self.client.listall(self.username, '*a')
        time.sleep(1)
        listall_reply = self.client.receive_message()
        # asserts server correctly received and processed listall request 
        self.assertEqual(listall_reply['metadata']['message_type'], SRV_LISTALL)
        # asserts filtering by wildcard filter is correct 
        for username in listall_reply['message_content']: 
            self.assertRegexpMatches(self.username, '*a')
       
    def test_del_user(self): 
        result = self.client.del_user()
        time.sleep(1)
        del_user_reply = self.client.receive_message()
        self.assertEqual(del_user_reply['metadata']['message_type'], SRV_DEL_USER)

    
if __name__ == '__main__':
    HOST = "192.168.0.114"
    unittest.main()