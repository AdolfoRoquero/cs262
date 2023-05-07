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
                response_deserializer=quiplash__pb2.JoinGameReply.FromString,
                )
        self.SendQuestions = channel.unary_unary(
                '/chatapp.Quiplash/SendQuestions',
                request_serializer=quiplash__pb2.QuestionList.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.SendAnswers = channel.unary_unary(
                '/chatapp.Quiplash/SendAnswers',
                request_serializer=quiplash__pb2.AnswerList.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.SendAllAnswers = channel.unary_unary(
                '/chatapp.Quiplash/SendAllAnswers',
                request_serializer=quiplash__pb2.AnswerList.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.SendVote = channel.unary_unary(
                '/chatapp.Quiplash/SendVote',
                request_serializer=quiplash__pb2.Vote.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.NotifyPlayers = channel.unary_unary(
                '/chatapp.Quiplash/NotifyPlayers',
                request_serializer=quiplash__pb2.GameNotification.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.NewUser_StateUpdate = channel.unary_unary(
                '/chatapp.Quiplash/NewUser_StateUpdate',
                request_serializer=quiplash__pb2.User.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.QuestionAssignment_StateUpdate = channel.unary_unary(
                '/chatapp.Quiplash/QuestionAssignment_StateUpdate',
                request_serializer=quiplash__pb2.QuestionList.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.UserAnswer_StateUpdate = channel.unary_unary(
                '/chatapp.Quiplash/UserAnswer_StateUpdate',
                request_serializer=quiplash__pb2.Answer.SerializeToString,
                response_deserializer=quiplash__pb2.RequestReply.FromString,
                )
        self.Vote_StateUpdate = channel.unary_unary(
                '/chatapp.Quiplash/Vote_StateUpdate',
                request_serializer=quiplash__pb2.Vote.SerializeToString,
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

    def SendQuestions(self, request, context):
        """Request from PRIMARY node to OTHER-NODES with questions to answer 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendAnswers(self, request, context):
        """Request from OTHER-NODES to PRIMARY node with answer to question 
        rpc SendAnswer(Answer) returns (RequestReply); 

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendAllAnswers(self, request, context):
        """Request from PRIMARY node to OTHER-NODES with all answers to all questions for voting.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendVote(self, request, context):
        """Request from OTHER-NODES to PRIMARY node with answer to question 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NotifyPlayers(self, request, context):
        """Server notification 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NewUser_StateUpdate(self, request, context):
        """Request to update replica state when a new user JOINS the game.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QuestionAssignment_StateUpdate(self, request, context):
        """Request to update replica state when a question is ASSIGNED to a user.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UserAnswer_StateUpdate(self, request, context):
        """Request to update replica state when a user ANSWERS a question.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Vote_StateUpdate(self, request, context):
        """Request to update replica state when a user VOTES for a quesiton.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_QuiplashServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'JoinGame': grpc.unary_unary_rpc_method_handler(
                    servicer.JoinGame,
                    request_deserializer=quiplash__pb2.User.FromString,
                    response_serializer=quiplash__pb2.JoinGameReply.SerializeToString,
            ),
            'SendQuestions': grpc.unary_unary_rpc_method_handler(
                    servicer.SendQuestions,
                    request_deserializer=quiplash__pb2.QuestionList.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'SendAnswers': grpc.unary_unary_rpc_method_handler(
                    servicer.SendAnswers,
                    request_deserializer=quiplash__pb2.AnswerList.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'SendAllAnswers': grpc.unary_unary_rpc_method_handler(
                    servicer.SendAllAnswers,
                    request_deserializer=quiplash__pb2.AnswerList.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'SendVote': grpc.unary_unary_rpc_method_handler(
                    servicer.SendVote,
                    request_deserializer=quiplash__pb2.Vote.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'NotifyPlayers': grpc.unary_unary_rpc_method_handler(
                    servicer.NotifyPlayers,
                    request_deserializer=quiplash__pb2.GameNotification.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'NewUser_StateUpdate': grpc.unary_unary_rpc_method_handler(
                    servicer.NewUser_StateUpdate,
                    request_deserializer=quiplash__pb2.User.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'QuestionAssignment_StateUpdate': grpc.unary_unary_rpc_method_handler(
                    servicer.QuestionAssignment_StateUpdate,
                    request_deserializer=quiplash__pb2.QuestionList.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'UserAnswer_StateUpdate': grpc.unary_unary_rpc_method_handler(
                    servicer.UserAnswer_StateUpdate,
                    request_deserializer=quiplash__pb2.Answer.FromString,
                    response_serializer=quiplash__pb2.RequestReply.SerializeToString,
            ),
            'Vote_StateUpdate': grpc.unary_unary_rpc_method_handler(
                    servicer.Vote_StateUpdate,
                    request_deserializer=quiplash__pb2.Vote.FromString,
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
            quiplash__pb2.JoinGameReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendQuestions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/SendQuestions',
            quiplash__pb2.QuestionList.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendAnswers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/SendAnswers',
            quiplash__pb2.AnswerList.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendAllAnswers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/SendAllAnswers',
            quiplash__pb2.AnswerList.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/SendVote',
            quiplash__pb2.Vote.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NotifyPlayers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/NotifyPlayers',
            quiplash__pb2.GameNotification.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def NewUser_StateUpdate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/NewUser_StateUpdate',
            quiplash__pb2.User.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def QuestionAssignment_StateUpdate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/QuestionAssignment_StateUpdate',
            quiplash__pb2.QuestionList.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UserAnswer_StateUpdate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/UserAnswer_StateUpdate',
            quiplash__pb2.Answer.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Vote_StateUpdate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/chatapp.Quiplash/Vote_StateUpdate',
            quiplash__pb2.Vote.SerializeToString,
            quiplash__pb2.RequestReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
