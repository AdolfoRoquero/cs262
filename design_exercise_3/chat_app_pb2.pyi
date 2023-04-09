from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChatMessage(_message.Message):
    __slots__ = ["date", "destinataries", "sender", "text"]
    DATE_FIELD_NUMBER: _ClassVar[int]
    DESTINATARIES_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    date: _timestamp_pb2.Timestamp
    destinataries: UserList
    sender: User
    text: str
    def __init__(self, sender: _Optional[_Union[User, _Mapping]] = ..., destinataries: _Optional[_Union[UserList, _Mapping]] = ..., text: _Optional[str] = ..., date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ListAllRequest(_message.Message):
    __slots__ = ["username_filter"]
    USERNAME_FILTER_FIELD_NUMBER: _ClassVar[int]
    username_filter: str
    def __init__(self, username_filter: _Optional[str] = ...) -> None: ...

class LogActionTypeReply(_message.Message):
    __slots__ = ["log_action"]
    class ActionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    DELETE_USER: LogActionTypeReply.ActionType
    DEQUEUE_MSG: LogActionTypeReply.ActionType
    ENQUEUE_MSG: LogActionTypeReply.ActionType
    LOG_ACTION_FIELD_NUMBER: _ClassVar[int]
    NEW_USER: LogActionTypeReply.ActionType
    log_action: LogActionTypeReply.ActionType
    def __init__(self, log_action: _Optional[_Union[LogActionTypeReply.ActionType, str]] = ...) -> None: ...

class RequestReply(_message.Message):
    __slots__ = ["reply", "request_status", "rerouted"]
    class RequestStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    FAILED: RequestReply.RequestStatus
    REPLY_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    REROUTED: RequestReply.RequestStatus
    REROUTED_FIELD_NUMBER: _ClassVar[int]
    SUCCESS: RequestReply.RequestStatus
    reply: str
    request_status: RequestReply.RequestStatus
    rerouted: str
    def __init__(self, reply: _Optional[str] = ..., request_status: _Optional[_Union[RequestReply.RequestStatus, str]] = ..., rerouted: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ["users"]
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[User]
    def __init__(self, users: _Optional[_Iterable[_Union[User, _Mapping]]] = ...) -> None: ...
