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
        """Execute self.command
        
            Returns the reply and the RequestReply type
        """
        if self.command == "sign_up":
            return self.server_stub.SignUp(self.user)

        elif self.command == "login":
            return self.server_stub.Login(self.user)

        elif self.command.startswith("listall"):
            username_filter = chat_app_pb2.ListAllRequest(
            username_filter = self.command.replace('listall', '').strip())
            return self.server_stub.ListAll(username_filter)

        elif self.command.startswith("delete_user"): 
            return self.server_stub.DeleteUser(self.user)

        elif self.command.startswith("send_message"): 
            msg_datetime = Timestamp()
            msg_datetime.GetCurrentTime()
            chat_message = chat_app_pb2.ChatMessage(
                sender = self.user,
                destinataries = chat_app_pb2.UserList(users=self.destinataries), 
                text = self.message, 
                date = msg_datetime)
            return self.server_stub.SendMessage(chat_message)

        elif self.command == "receive_message":
            return self.server_stub.ReceiveMessage(self.user) 

        else:
            raise ValueError("Command type is not recognized")

    
    def run_command(self):
        """ Run command by rerouting until a maximum number of attempts is reached"""
        print(f"Running {self.command}")
        reply = self.single_execute()
        print("First \n", reply)
        attempts = 0
        while reply.request_status != chat_app_pb2.SUCCESS:
            print("Execution was not successful")
            
            if attempts > self.max_num_attempts:
                print("Max number of retries reached")
                break

            if reply.request_status != chat_app_pb2.REROUTED:
                print(f"\tRerouting to server {reply.rerouted}") 
                self.primary_server = reply.rerouted
                self.server_stub = self.replica_stubs[self.primary_server]
            elif reply.request_status != chat_app_pb2.FAILED:
                print("\tTrying new server")

            reply = self.single_execute()
            attempts += 1
        return reply



    def run(self): 
        # Login/SignUp routine 
        while True: 
            register_or_login = input("New or existing user (N or E): ").strip().lower()
            if register_or_login == 'n':
                username = input("Enter username: ").strip().lower()
                self.command = "sign_up" 
                self.user = chat_app_pb2.User(username = username)
                reply = self.run_command()
                # TODO: Check final reply
                break
            elif register_or_login == 'e': 
                username = input("Enter username: ").strip().lower()
                self.user = chat_app_pb2.User(username = username)
                self.command = "login" 
                reply = self.run_command()
                # TODO: Check final reply                
                break
            

            # if (reply.request_reply.request_status == chat_app_pb2.SUCCESS): 
            #     # Receive messages pending from previous session
            #     replies = self.server_stub.ReceiveMessage(self.user) 

            #     for reply in replies:
            #         print(f'{reply.sender.username} > {reply.text}')
            #     break
        self.command = ''
        print("\n\n\nEND LOGIN/SIGNUP\n\n\n")

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
                if reply.request_status == chat_app_pb2.SUCCESS: 
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