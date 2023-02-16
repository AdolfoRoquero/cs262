from concurrent import futures

import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict


class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server.
    """
    def __init__(self):
        self.registered_users = chat_app_pb2.UserList()
        self.pending_messages = defaultdict(list) 


    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        request_reply = chat_app_pb2.RequestReply()
        if request in self.registered_users.users: 
            request_reply.reply = 'Success'
        else: 
            request_reply.reply = 'Failure, username not registered'
        return request_reply

    def SignUp(self, request, context):
        request_reply = chat_app_pb2.RequestReply()
        if request not in self.registered_users.users: 
            request_reply.reply = 'Success'
            self.registered_users.users.append(request)
        else: 
            request_reply.reply = 'Failure, username taken'
        return request_reply

    def ListAll(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendMessage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReceiveMessage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(ChatAppServicer(), server)
    server.add_insecure_port('127.0.0.1:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

