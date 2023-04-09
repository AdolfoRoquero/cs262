import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 
import config

class Client():
    def __init__(self, rep_servers_config, primary_server):
        
        self.rep_servers_config = rep_servers_config
        
        # Initialize a stub for every server
        self.replica_stubs = {}
        for rep_server in self.rep_servers_config:
            channel = grpc.insecure_channel(f"{self.rep_servers_config[rep_server]['host']}:{self.rep_servers_config[rep_server]['port']}")
            self.replica_stubs[rep_server] = chat_app_pb2_grpc.ChatAppStub(channel)

        assert primary_server in self.rep_servers_config, f"Server id {primary_server} is not valid"
        self.primary_server = primary_server
        self.server_stub = self.replica_stubs[self.primary_server]
        

        # Number of attempts to reroute
        self.max_num_attempts = len(self.replica_stubs) 


    def single_execute(self):
        if self.command.startswith("listall"):
            username_filter = chat_app_pb2.ListAllRequest(
            username_filter = self.command.replace('listall', '').strip())
            reply = self.server_stub.ListAll(username_filter)

        elif self.command.startswith("delete_user"): 
            reply = self.server_stub.DeleteUser(self.user)

        elif self.command.startswith("send_message"): 
            msg_datetime = Timestamp()
            msg_datetime.GetCurrentTime()
            chat_message = chat_app_pb2.ChatMessage(
                sender = self.user,
                destinataries = chat_app_pb2.UserList(users=self.destinataries), 
                text = self.message, 
                date = msg_datetime)
            reply = self.server_stub.SendMessage(chat_message)

        elif self.command == "receive_message":
            reply = self.server_stub.ReceiveMessage(self.user) 
        
        else:
            raise ValueError("Command type is not recognized")

        return reply
    
    def run_command(self):
        """ Run command by rerouting until a maximum number of attempts is reached"""

        reply = self.single_execute()
        attempts = 0
        while reply.request_status != chat_app_pb2.RequestReply.SUCCESS:
            if attempts > self.max_num_attempts:
                print("Max number of retries reached")
                break
            if reply.request_status != chat_app_pb2.RequestReply.REROUTED:
                print(f"Rerouting to server {reply.rerouted}") 
                self.primary_server = reply.rerouted
                self.server_stub = self.replica_stubs[self.primary_server]
            elif reply.request_status != chat_app_pb2.RequestReply.FAILED:
                print("Trying new server")
            reply =  self.single_execute()
            attempts += 1
            
        return reply



    def run(self): 
        # Login/SignUp routine 
        while True: 
            register_or_login = input("New or existing user (N or E): ").strip().lower()
            username = input("Enter username: ").strip().lower()
            if register_or_login == 'n': 
                self.user = chat_app_pb2.User(username = username)
                reply = self.server_stub.SignUp(self.user)
            elif register_or_login == 'e': 
                self.user = chat_app_pb2.User(username = username)
                reply = self.server_stub.Login(self.user)
            if ((reply.request_status == chat_app_pb2.RequestReply.SUCCESS) and
                (reply.reply == 'Success')): 
                # Receive messages pending from previous session
                replies = self.server_stub.ReceiveMessage(self.user) 

                for reply in replies:
                    print(f'{reply.sender.username} > {reply.text}')
                break
        self.command = ''

        while True: 
            print(f"Commands: 'listall <wildcard>', 'delete_user', 'send_message' OR <enter> to refresh")
            self.command = input(f"{self.user.username}> ").strip()

            if self.command.startswith("send_message"): 
                dest = input(f"{self.user.username}> Destinataries (comma separated): ").strip().lower()
                self.destinataries = [chat_app_pb2.User(username = destinatary.strip()) for destinatary in dest.split(",")]
                self.message = input(f"{self.user}> Message: ").strip()

            # Run command until a server processes it.
            reply = self.run_command()

            if self.command.startswith("listall"):
                print(f'{username} > {",".join([user.username for user in reply.users])}')
            elif self.command.startswith("delete_user"): 
                if reply.request_status == chat_app_pb2.RequestReply.SUCCESS: 
                    print(f"User {self.user.username} deleted.")
                    break 
                else: 
                    print("Unable to delete user.")
            
            self.command = ''
            self.destinataries = None
            self.message = None

            # Receive messages pending
            self.command = 'receive_message' 
            replies = self.run_command()

            for reply in replies:
                print(f'{reply.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")} {reply.sender.username} > {reply.text}')
            
            self.command = ''
        
if __name__ == "__main__":
    client = Client(config.CONFIG, config.STARTING_PRIMARY_SERVER)

    client.run()