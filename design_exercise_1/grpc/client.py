import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf import timestamp_pb2 
import grpc

def run():
    with grpc.insecure_channel('10.250.227.245:50051') as channel:
        stub = chat_app_pb2_grpc.ChatAppStub(channel)
        while True: 
            register_or_login = input("New or Existing user: ").strip().lower()
            username = input("Username: ").strip().lower()
            if register_or_login == 'n': 
                user = chat_app_pb2.User(username = username)
                reply = stub.SignUp(user)
            elif register_or_login == 'e': 
                user = chat_app_pb2.User(username = username)
                reply = stub.Login(user)
            print(reply.reply)
            if reply.reply == 'Success': 
                # Receive messages pending from previous session
                replies = stub.ReceiveMessage(user) 

                for reply in replies:
                    print(f'{reply.sender.username} > {reply.text}')
                break
        
        while True: 
            destinataries = input(f"{username}> Destinataries: ").strip()
            if destinataries.startswith("listall"):
                username_filter = chat_app_pb2.ListAllRequest(
                username_filter = destinataries.replace('listall', '').strip())
                reply = stub.ListAll(username_filter) 
                print(f'{username} > {",".join([user.username for user in reply.users])}')

            elif destinataries.startswith("delete_user"): 
                reply = stub.DeleteUser(user)
                if reply.request_status == 1: 
                    print(f"User {user.username} deleted.")
                    break 
                else: 
                    print("Unable to delete user.")
            
            elif destinataries: 
                destinataries = [chat_app_pb2.User(username = dest.strip()) for dest in destinataries.split(",")]
                message = input(f"{user.username}> Message: ").strip()
                if message: 
                    chat_message = chat_app_pb2.ChatMessage(
                        sender = user, destinataries = chat_app_pb2.UserList(users=destinataries), 
                        text = message, date = timestamp_pb2.Timestamp().GetCurrentTime())
                    reply = stub.SendMessage(chat_message)

            # Receive messages pending 
            replies = stub.ReceiveMessage(user) 

            for reply in replies:
                print(f'{reply.sender.username} > {reply.text}')


            
                
                    

       
        
if __name__ == "__main__":
    run()