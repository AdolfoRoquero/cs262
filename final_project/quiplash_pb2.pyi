from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
FAILED: RequestStatus
REROUTED: RequestStatus
SUCCESS: RequestStatus

class Answer(_message.Message):
    __slots__ = ["answer_text", "question_id", "respondent"]
    ANSWER_TEXT_FIELD_NUMBER: _ClassVar[int]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONDENT_FIELD_NUMBER: _ClassVar[int]
    answer_text: str
    question_id: str
    respondent: User
    def __init__(self, respondent: _Optional[_Union[User, _Mapping]] = ..., answer_text: _Optional[str] = ..., question_id: _Optional[str] = ...) -> None: ...

class AnswerList(_message.Message):
    __slots__ = ["answer_list"]
    ANSWER_LIST_FIELD_NUMBER: _ClassVar[int]
    answer_list: _containers.RepeatedCompositeFieldContainer[Answer]
    def __init__(self, answer_list: _Optional[_Iterable[_Union[Answer, _Mapping]]] = ...) -> None: ...

class GameNotification(_message.Message):
    __slots__ = ["text", "type"]
    class NotificationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    GAME_START: GameNotification.NotificationType
    QUESTION_TIMEOUT: GameNotification.NotificationType
    SCORING_START: GameNotification.NotificationType
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VOTING_START: GameNotification.NotificationType
    text: str
    type: GameNotification.NotificationType
    def __init__(self, type: _Optional[_Union[GameNotification.NotificationType, str]] = ..., text: _Optional[str] = ...) -> None: ...

class JoinGameReply(_message.Message):
    __slots__ = ["existing_players", "game_status", "num_players", "request_status"]
    class GameStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    EXISTING_PLAYERS_FIELD_NUMBER: _ClassVar[int]
    GAME_STATUS_FIELD_NUMBER: _ClassVar[int]
    NUM_PLAYERS_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTED: JoinGameReply.GameStatus
    WAITING: JoinGameReply.GameStatus
    existing_players: _containers.RepeatedCompositeFieldContainer[User]
    game_status: JoinGameReply.GameStatus
    num_players: int
    request_status: RequestStatus
    def __init__(self, num_players: _Optional[int] = ..., request_status: _Optional[_Union[RequestStatus, str]] = ..., game_status: _Optional[_Union[JoinGameReply.GameStatus, str]] = ..., existing_players: _Optional[_Iterable[_Union[User, _Mapping]]] = ...) -> None: ...

class LivenessRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LivenessResponse(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class Question(_message.Message):
    __slots__ = ["destinatary", "question_id", "question_text", "topic"]
    DESTINATARY_FIELD_NUMBER: _ClassVar[int]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    QUESTION_TEXT_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    destinatary: User
    question_id: str
    question_text: str
    topic: str
    def __init__(self, question_id: _Optional[str] = ..., question_text: _Optional[str] = ..., topic: _Optional[str] = ..., destinatary: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class QuestionList(_message.Message):
    __slots__ = ["question_list"]
    QUESTION_LIST_FIELD_NUMBER: _ClassVar[int]
    question_list: _containers.RepeatedCompositeFieldContainer[Question]
    def __init__(self, question_list: _Optional[_Iterable[_Union[Question, _Mapping]]] = ...) -> None: ...

class RequestReply(_message.Message):
    __slots__ = ["reply", "request_status", "rerouted"]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    REROUTED_FIELD_NUMBER: _ClassVar[int]
    reply: str
    request_status: RequestStatus
    rerouted: str
    def __init__(self, reply: _Optional[str] = ..., request_status: _Optional[_Union[RequestStatus, str]] = ..., rerouted: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["ip_address", "port", "username"]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    ip_address: str
    port: str
    username: str
    def __init__(self, username: _Optional[str] = ..., ip_address: _Optional[str] = ..., port: _Optional[str] = ...) -> None: ...

class Vote(_message.Message):
    __slots__ = ["question_id", "votee", "voter"]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    VOTEE_FIELD_NUMBER: _ClassVar[int]
    VOTER_FIELD_NUMBER: _ClassVar[int]
    question_id: str
    votee: User
    voter: User
    def __init__(self, voter: _Optional[_Union[User, _Mapping]] = ..., question_id: _Optional[str] = ..., votee: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class RequestStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
