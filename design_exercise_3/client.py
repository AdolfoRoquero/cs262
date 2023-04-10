import chat_app_pb2_grpc
import chat_app_pb2
from google.protobuf.timestamp_pb2 import Timestamp
import grpc
import os 
import config
from enum import Enum

def terminal_command_is_valid(command):
    if command == "send_message":
        return True
    if command == "delete_user":
        return True
    if command.startswith("listall"):
        return True
    if (command == "") or (command == "\n"):
        return True
    return False


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
        self.max_num_attempts = len(self.rep_servers_config) 


    def single_execute(self):
        """Execute self.command
           Returns the reply
        """
        if self.command == "sign_up":
            return self.server_stub.SignUp(self.user, timeout=0.5)

        elif self.command == "login":
            return self.server_stub.Login(self.user, timeout=0.5)

        elif self.command.startswith("listall"):
            username_filter = chat_app_pb2.ListAllRequest(
            username_filter = self.command.replace('listall', '').strip())
            return self.server_stub.ListAll(username_filter, timeout=0.5)

        elif self.command.startswith("delete_user"): 
            return self.server_stub.DeleteUser(self.user, timeout=0.5)

        elif self.command.startswith("send_message"): 
            msg_datetime = Timestamp()
            msg_datetime.GetCurrentTime()
            chat_message = chat_app_pb2.ChatMessage(
                sender = self.user,
                destinataries = chat_app_pb2.UserList(users=self.destinataries), 
                text = self.message, 
                date = msg_datetime)
            return self.server_stub.SendMessage(chat_message, timeout=0.5)

        elif self.command == "receive_message":
            return self.server_stub.ReceiveMessage(self.user, timeout=0.5) 

        else:
            raise ValueError("Command type is not recognized")
    
        
    def run_command(self):
        """ Run command until it is processed by a server
            If the primary server is down, this function 
            will try communicating with the other servers  
        """
        attempts = 0
        servers = sorted(self.rep_servers_config)
        resend = False 
        try:
            reply = self.single_execute()
        except grpc.RpcError as e:
            self.primary_server = servers[(servers.index(self.primary_server) + 1) % 3]
            print(f"New primary {self.primary_server}")
            self.server_stub = self.replica_stubs[self.primary_server]
            resend = True

        while resend or (reply.request_status != chat_app_pb2.SUCCESS):
            if attempts > self.max_num_attempts:
                print("Max number of retries reached")
                break

            if not resend:
                if reply.request_status == chat_app_pb2.REROUTED:
                    print(f"\tRerouting to server {reply.rerouted}") 
                    self.primary_server = reply.rerouted
                    self.server_stub = self.replica_stubs[self.primary_server]
                elif reply.request_status == chat_app_pb2.FAILED:
                    break    
            try: 
                reply = self.single_execute()
                resend = False 
            except grpc.RpcError as e:
                resend = True 
                self.primary_server = servers[(servers.index(self.primary_server) + 1) % 3]
                self.server_stub = self.replica_stubs[self.primary_server]            
        
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
            elif register_or_login == 'e': 
                username = input("Enter username: ").strip().lower()
                self.user = chat_app_pb2.User(username = username)
                self.command = "login" 
                reply = self.run_command()

            if reply.request_status == chat_app_pb2.FAILED:
                print(reply.reply)
            else:
                break

        # Receives any pending messages on login
        self.command = 'receive_message'
        replies = self.run_command()

        for reply in replies.messages:
            print(f'{reply.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")} {reply.sender.username} > {reply.text}')
        
        while True: 
            print(f"Commands: 'listall <wildcard>', 'delete_user', 'send_message' OR <enter> to refresh")
            self.command = input(f"{self.user.username}> ").strip()
            
            while not terminal_command_is_valid(self.command):
                print(f"Commands: 'listall <wildcard>', 'delete_user', 'send_message' OR <enter> to refresh")
                self.command = input(f"{self.user.username}> ").strip()

            if not self.command:
                self.command = "receive_message"
                replies = self.run_command()

                for reply in replies.messages:
                    print(f'{reply.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")} {reply.sender.username} > {reply.text}')


            elif self.command.startswith("send_message"): 
                dest = input(f"{self.user.username}> Destinataries (comma separated): ").strip().lower()
                self.destinataries = [chat_app_pb2.User(username = destinatary.strip()) for destinatary in dest.split(",")]
                self.message = input(f"{self.user.username}> Message: ").strip()
                # Run command until a server processes it.
                reply = self.run_command()

            elif self.command.startswith("listall"):
                reply = self.run_command()
                print(f'{username} > {",".join([user.username for user in reply.users])}')
            elif self.command.startswith("delete_user"): 
                reply = self.run_command()
                if reply.request_status == chat_app_pb2.SUCCESS: 
                    print(f"User {self.user.username} deleted.")
                    break 
                else: 
                    print("Unable to delete user.")
            
            if self.command != 'receive_message': 
                self.command = 'receive_message'
                replies = self.run_command()
                for reply in replies.messages:
                    print(f'{reply.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")} {reply.sender.username} > {reply.text}')

                    
if __name__ == "__main__":
    client = Client(config.CONFIG, config.STARTING_PRIMARY_SERVER)
    client.run()