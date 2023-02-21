from concurrent import futures

import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict
import fnmatch 


class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server.
    """
    def __init__(self):
        test_user = chat_app_pb2.User(username = 'test123')
        users = [test_user]
        self.registered_users = chat_app_pb2.UserList()
        self.registered_users.users.extend(users)
        self.pending_messages = defaultdict(list) 

    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        if request in self.registered_users.users: 
            return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
        else: 
            return chat_app_pb2.RequestReply(reply = 'Failure, username not registered',
             request_status = 0)

    def SignUp(self, request, context):
        if request not in self.registered_users.users: 
            self.registered_users.users.append(request)
            return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
        else: 
            return chat_app_pb2.RequestReply(reply = 'Failure, username taken', request_status = 0)

    def ListAll(self, request, context):
        filtered_users = chat_app_pb2.UserList()
        filtered_users.users.extend([user for user in self.registered_users.users if fnmatch.fnmatch(user.username, request.username_filter)])
        return filtered_users

    def DeleteUser(self, request, context):
        updated_registered_users = chat_app_pb2.UserList()
        for user in self.registered_users.users:
            if user.username != request.username: 
                updated_registered_users.users.append(user)
        if len(self.registered_users.users) - 1 == len(updated_registered_users.users): 
            self.registered_users = updated_registered_users
            return chat_app_pb2.RequestReply(request_status = 1)
        else: 
            return chat_app_pb2.RequestReply(request_status = 0)

    def SendMessage(self, request, context):
        destinataries = request.destinataries.users
        request.ClearField('destinataries')
        for destinatary in destinataries:
    
            if destinatary in self.registered_users.users: 
                self.pending_messages[destinatary.username].append(request)
        #TODO reply 
        return chat_app_pb2.RequestReply(request_status = 1)
         
    def ReceiveMessage(self, request, context):
        for message in self.pending_messages[request.username]: 
            yield message
        
        del self.pending_messages[request.username] 
        


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(ChatAppServicer(), server)
    server.add_insecure_port('192.168.0.114:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

