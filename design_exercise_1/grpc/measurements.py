import string 
import random 
import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 


def run(): 
    host = '127.0.0.1'
    port = '50051'
    channel = host + ':' + port

    username = 't'
    with grpc.insecure_channel(f'{host}:{port}') as channel:
        stub = chat_app_pb2_grpc.ChatAppStub(channel)
        user = chat_app_pb2.User(username = username)
        print(f'CLIENT signup message: {user.ByteSize()}')
        print(f'CLIENT login message: {user.ByteSize()}')
        reply = stub.SignUp(user)
        print(f'SERVER login message reply: {reply.ByteSize()}')

        # listall message size 
        username_filter = chat_app_pb2.ListAllRequest(username_filter = '*')
        reply = stub.ListAll(username_filter) 
        print(f'CLIENT listall "*": {username_filter.ByteSize()}')
        print(f'SERVER listall reply "*": {reply.ByteSize()}')

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
        reply = stub.SendMessage(chat_message)
        print(f'CLIENT send message "{msg_text}": {chat_message.ByteSize()}')
        print(f'SERVER send message reply: {reply.ByteSize()}')

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
        reply = stub.SendMessage(chat_message)
        print(f'SERVER send message reply: {reply.ByteSize()}')


        # delete_user message size 
        print(f'CLIENT delete user: {user.ByteSize()}')
        reply = stub.DeleteUser(user)
        print(f'SERVER delete user reply: {reply.ByteSize()}')
        # receive message size 
        print(f'CLIENT receive message: {user.ByteSize()}')


if __name__ == "__main__":
    run()  

