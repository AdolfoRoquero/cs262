import string 
import random 
import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 


def run(): 
    host = '192.168.0.114'
    port = '50051'
    channel = host + ':' + port

    username = 't'
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = chat_app_pb2_grpc.ChatAppStub(channel)
        user = chat_app_pb2.User(username = username)
        print(f'CLIENT signup message: {user.ByteSize()}')
        print(f'CLIENT login message: {user.ByteSize()}')
        reply = stub.SignUp(user)

        # listall message size 
        username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
        # reply = stub.ListAll(username_filter) 
        print(f'CLIENT listall "*": {username_filter.ByteSize()}')

        # listall message size with filter
        letters = string.ascii_lowercase
        random_filter = ''.join(random.choice(letters) for i in range(8))
        username_filter = chat_app_pb2.ListAllRequest(username_filter = '*' + random_filter)
        print(f'CLIENT listall {"*" + random_filter}: {username_filter.ByteSize()}')

        # send message message size 
        message = ""
        destinatary = "a"
        msg_datetime = Timestamp()
        msg_datetime.GetCurrentTime()
        msg_text = ''
        user2 = chat_app_pb2.User(username = destinatary)
        chat_message = chat_app_pb2.ChatMessage(
                            sender = user, destinataries = chat_app_pb2.UserList(users=[user2]), 
                            text = msg_text, date = msg_datetime)
        print(f'CLIENT send message "{msg_text}": {chat_message.ByteSize()}')

        # send message message size 
        message = ""
        destinatary = "a"
        msg_datetime = Timestamp()
        msg_datetime.GetCurrentTime()
        msg_text = 'Hello'
        chat_message = chat_app_pb2.ChatMessage(
                            sender = user, destinataries = chat_app_pb2.UserList(users=[user2]), 
                            text = msg_text, date = msg_datetime)
        print(f'CLIENT send message "{msg_text}": {chat_message.ByteSize()}')

        # delete_user message size 
        print(f'CLIENT delete user: {user.ByteSize()}')

        # receive message size 
        print(f'CLIENT receive message: {user.ByteSize()}')


if __name__ == "__main__":
    run()  

