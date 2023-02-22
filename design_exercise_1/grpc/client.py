import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 

def run():
    HOST = os.environ['CHAT_APP_SERVER_HOST']
    PORT = os.environ['CHAT_APP_SERVER_PORT']
    channel_ = HOST + ':' + PORT
    with grpc.insecure_channel(channel_) as channel:
        stub = chat_app_pb2_grpc.ChatAppStub(channel)
        while True: 
            register_or_login = input("New or existing user (N or E): ").strip().lower()
            username = input("Enter username: ").strip().lower()
            if register_or_login == 'n': 
                user = chat_app_pb2.User(username = username)
                reply = stub.SignUp(user)
            elif register_or_login == 'e': 
                user = chat_app_pb2.User(username = username)
                reply = stub.Login(user)
            if reply.reply == 'Success': 
                # Receive messages pending from previous session
                replies = stub.ReceiveMessage(user) 

                for reply in replies:
                    print(f'{reply.sender.username} > {reply.text}')
                break
        command = ''
        while True: 
            print(f"Commands: 'listall <wildcard>', 'delete_user', 'send_message' OR <enter> to refresh")
            command = input(f"{username}> ").strip()
            if command.startswith("listall"):
                username_filter = chat_app_pb2.ListAllRequest(
                username_filter = command.replace('listall', '').strip())
                reply = stub.ListAll(username_filter) 
                print(f'{username} > {",".join([user.username for user in reply.users])}')
                command = ''

            elif command.startswith("delete_user"): 
                reply = stub.DeleteUser(user)
                if reply.request_status == 1: 
                    print(f"User {user.username} deleted.")
                    break 
                else: 
                    print("Unable to delete user.")
                command = ''
            
            elif command.startswith("send_message"): 
                dest = input(f"{username}> Destinataries (comma separated): ").strip().lower()
                destinataries = [chat_app_pb2.User(username = destinatary.strip()) for destinatary in dest.split(",")]
                message = input(f"{user.username}> Message: ").strip()
                if message: 
                    msg_datetime = Timestamp()
                    msg_datetime.GetCurrentTime()
                    chat_message = chat_app_pb2.ChatMessage(
                        sender = user, destinataries = chat_app_pb2.UserList(users=destinataries), 
                        text = message, date = msg_datetime)
                    reply = stub.SendMessage(chat_message)
                command = ''

            # Receive messages pending 
            replies = stub.ReceiveMessage(user) 

            for reply in replies:
                print(reply.date)
                print(f'{reply.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")} {reply.sender.username} > {reply.text}')


            
                
                    

       
        
if __name__ == "__main__":
    run()