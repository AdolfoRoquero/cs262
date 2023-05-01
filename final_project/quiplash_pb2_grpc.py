# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import quiplash_pb2 as quiplash__pb2


class QuiplashStub(object):
    """Interface exported by the server.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.JoinGame = channel.unary_unary(
                '/chatapp.Quiplash/JoinGame',
                request_serializer=quiplash__pb2.User.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.AskQuestion = channel.unary_unary(
                '/chatapp.Quiplash/AskQuestion',
                request_serializer=quiplash__pb2.Question.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )


class QuiplashServicer(object):
    """Interface exported by the server.
    """

    def JoinGame(self, request, context):
        """Request to enter as a User into a game 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AskQuestion(self, request, context):
        """Request from primary server 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_QuiplashServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'JoinGame': grpc.unary_unary_rpc_method_handler(
                    servicer.JoinGame,
                    request_deserializer=quiplash__pb2.User.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'AskQuestion': grpc.unary_unary_rpc_method_handler(
                    servicer.AskQuestion,
                    request_deserializer=quiplash__pb2.Question.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'chatapp.Quiplash', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Quiplash(object):
    """Interface exported by the server.
    """

    @staticmethod
    def JoinGame(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/JoinGame',
            quiplash__pb2.User.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AskQuestion(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/AskQuestion',
            quiplash__pb2.Question.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)