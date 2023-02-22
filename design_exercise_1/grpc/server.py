"""Chat App - GRPC ChatAppServicer Class

This script defines the GRPC ChatAppServicer class that implements the Wire Protocol (as defined in `chat_app.proto`)

This file can be imported as a module and can ALSO be run to spawn a running server.
"""

from concurrent import futures
import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict
import fnmatch 
import os


class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server."""
    def __init__(self):
        root_user = chat_app_pb2.User(username = 'root')
        self.registered_users = chat_app_pb2.UserList()
        self.registered_users.users.extend([root_user])
        self.pending_messages = defaultdict(list) 

    def Login(self, request, context):
        """
        Logs in user into the platform if the username already exists.

        Parameters
        ----------
        request : User (chat_app.proto)
            User to log in. 

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the login attempt.
        """

        if request in self.registered_users.users: 
            print(f'user login success {request.username}')
            return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
        else: 
            print(f'user login failure {request.username}')
            return chat_app_pb2.RequestReply(reply = 'Failure, username not registered',
             request_status = 0)

    def SignUp(self, request, context):
        """
        Sign up new user into the platform (only if the username is not taken).

        Parameters
        ----------
        request : User (chat_app.proto)
            User to sign up. 

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the signup attempt.
        """
        if request not in self.registered_users.users: 
            self.registered_users.users.append(request)
            print(f'user signup success {request.username}')
            return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
        else: 
            print(f'user signup failed {request.username}')
            return chat_app_pb2.RequestReply(reply = 'Failure, username taken', request_status = 0)

    def ListAll(self, request, context):
        """
        Sign up new user into the platform (only if the username is not taken).

        Parameters
        ----------
        request : ListAllRequest (chat_app.proto)
            Username Filter based on which to filter users.

        Returns
        -------
        UserList :
            List of all users that match the filter.
        """

        filtered_users = chat_app_pb2.UserList()
        if request.username_filter:
            filtered_users.users.extend([user for user in self.registered_users.users 
                                     if fnmatch.fnmatch(user.username, request.username_filter) 
                                     and (user.username != 'root')])
        else:
            filtered_users.users.extend([user for user in self.registered_users.users if (user.username != 'root')])
            
        return filtered_users

    def DeleteUser(self, request, context):
        """
        Delete user from the chat app.

        Parameters
        ----------
        request : User (chat_app.proto)
            Username to be removed.

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the deletion.
        """
        print("Len reg users ", len(self.registered_users.users))
        updated_registered_users = chat_app_pb2.UserList()
        for user in self.registered_users.users:
            if user.username != request.username: 
                print("\nappend", user.username )
                updated_registered_users.users.append(user)
        if len(self.registered_users.users) - 1 == len(updated_registered_users.users): 
            self.registered_users = updated_registered_users
            return chat_app_pb2.RequestReply(request_status = 1)
        else: 
            return chat_app_pb2.RequestReply(request_status = 0)

    def SendMessage(self, request, context):
        """
        Queues message to be received by the specified destinatary. 

        Parameters
        ----------
        request : ChatMessage (chat_app.proto)
            Message to be sent (ChatMessage contains all data).

        Returns
        -------
        RequestReply :
            Indicates Success or Failure.
        """

        destinataries = request.destinataries.users
        request.ClearField('destinataries')
        for destinatary in destinataries:
            if destinatary in self.registered_users.users: 
                self.pending_messages[destinatary.username].append(request)
        return chat_app_pb2.RequestReply(request_status = 1)
         
    def ReceiveMessage(self, request, context):
        """
        Retrieves all messages for a given user. 

        Parameters
        ----------
        request : User (chat_app.proto)
            User for which to fetch all of the messages.

        Returns
        -------
        ChatMessage stream:
            Stream of all of the pending messages for the given user.
        """
        for message in self.pending_messages[request.username]: 
            yield message
        
        del self.pending_messages[request.username] 
        


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(ChatAppServicer(), server)
    HOST = os.environ['CHAT_APP_SERVER_HOST']
    PORT = os.environ['CHAT_APP_SERVER_PORT']
    server.add_insecure_port(f'{HOST}:{PORT}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

