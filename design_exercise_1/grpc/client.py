import chat_app_pb2_grpc
import chat_app_pb2
import time
import grpc

def run():
    with grpc.insecure_channel('127.0.0.1:50051') as channel:
        stub = chat_app_pb2_grpc.ChatAppStub(channel)
        while True: 
            register_or_login = input("New or Existing user: ")
            username = input("Username: ") 
            if register_or_login == 'N': 
                request = chat_app_pb2.User(username = username)
                reply = stub.SignUp(request)
            else: 
                request = chat_app_pb2.User(username = username)
                reply = stub.Login(request)
            print(reply.reply)
            if reply.reply == 'Success': 
                break
        
        while True: 
            input("Enter message here: ")

        
if __name__ == "__main__":
    run()