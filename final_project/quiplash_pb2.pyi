from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
FAILED: RequestStatus
REROUTED: RequestStatus
SUCCESS: RequestStatus

class Answer(_message.Message):
    __slots__ = ["answer_id", "answer_text", "question_id", "respondent"]
    ANSWER_ID_FIELD_NUMBER: _ClassVar[int]
    ANSWER_TEXT_FIELD_NUMBER: _ClassVar[int]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONDENT_FIELD_NUMBER: _ClassVar[int]
    answer_id: str
    answer_text: str
    question_id: str
    respondent: User
    def __init__(self, answer_id: _Optional[str] = ..., respondent: _Optional[_Union[User, _Mapping]] = ..., answer_text: _Optional[str] = ..., question_id: _Optional[str] = ...) -> None: ...

class LivenessRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LivenessResponse(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class Question(_message.Message):
    __slots__ = ["question_id", "question_text", "topic"]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    QUESTION_TEXT_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    question_id: str
    question_text: str
    topic: str
    def __init__(self, question_id: _Optional[str] = ..., question_text: _Optional[str] = ..., topic: _Optional[str] = ...) -> None: ...

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
    __slots__ = ["ip_address", "username"]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    ip_address: str
    username: str
    def __init__(self, username: _Optional[str] = ..., ip_address: _Optional[str] = ...) -> None: ...

class Vote(_message.Message):
    __slots__ = ["answer_id", "question_id", "voter"]
    ANSWER_ID_FIELD_NUMBER: _ClassVar[int]
    QUESTION_ID_FIELD_NUMBER: _ClassVar[int]
    VOTER_FIELD_NUMBER: _ClassVar[int]
    answer_id: str
    question_id: str
    voter: User
    def __init__(self, voter: _Optional[_Union[User, _Mapping]] = ..., question_id: _Optional[str] = ..., answer_id: _Optional[str] = ...) -> None: ...

class RequestStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
