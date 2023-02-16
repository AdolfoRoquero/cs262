from concurrent import futures

import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict


class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server.
    """
    # def __init__(self, host=socket.gethostname(), 
    #                    port=6000, 
    #                    timeout=60, 
    #                    usernames=["Leticia", "Liz", "Bel"],
    #                    clients={},
    #                    pending_messages=defaultdict(list)):
    def __init__(self):
        self.users = []
        self.pending_messages = defaultdict(list) 


    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        print(request.user)

        if request.user in self.users:
            pass

        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SignUp(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

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
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(
        ChatAppServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()