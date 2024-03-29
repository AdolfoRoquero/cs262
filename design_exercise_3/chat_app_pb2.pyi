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

class ChatMessageList(_message.Message):
    __slots__ = ["messages", "request_status", "rerouted"]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    REROUTED_FIELD_NUMBER: _ClassVar[int]
    messages: _containers.RepeatedCompositeFieldContainer[ChatMessage]
    request_status: RequestStatus
    rerouted: str
    def __init__(self, messages: _Optional[_Iterable[_Union[ChatMessage, _Mapping]]] = ..., request_status: _Optional[_Union[RequestStatus, str]] = ..., rerouted: _Optional[str] = ...) -> None: ...

class ListAllRequest(_message.Message):
    __slots__ = ["username_filter"]
    USERNAME_FILTER_FIELD_NUMBER: _ClassVar[int]
    username_filter: str
    def __init__(self, username_filter: _Optional[str] = ...) -> None: ...

class LivenessRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class LivenessResponse(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: str
    def __init__(self, status: _Optional[str] = ...) -> None: ...

class Log(_message.Message):
    __slots__ = ["action", "chat_message", "user"]
    class LogType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ACTION_FIELD_NUMBER: _ClassVar[int]
    CHAT_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DEL_USER: Log.LogType
    DEQUEUE_MSG: Log.LogType
    ENQUEUE_MSG: Log.LogType
    NEW_USER: Log.LogType
    USER_FIELD_NUMBER: _ClassVar[int]
    action: Log.LogType
    chat_message: ChatMessage
    user: User
    def __init__(self, action: _Optional[_Union[Log.LogType, str]] = ..., chat_message: _Optional[_Union[ChatMessage, _Mapping]] = ..., user: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class RebootRequest(_message.Message):
    __slots__ = ["last_entry"]
    LAST_ENTRY_FIELD_NUMBER: _ClassVar[int]
    last_entry: int
    def __init__(self, last_entry: _Optional[int] = ...) -> None: ...

class RebootResponse(_message.Message):
    __slots__ = ["last_entry", "log_diff"]
    LAST_ENTRY_FIELD_NUMBER: _ClassVar[int]
    LOG_DIFF_FIELD_NUMBER: _ClassVar[int]
    last_entry: int
    log_diff: _containers.RepeatedCompositeFieldContainer[Log]
    def __init__(self, last_entry: _Optional[int] = ..., log_diff: _Optional[_Iterable[_Union[Log, _Mapping]]] = ...) -> None: ...

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
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ["request_status", "rerouted", "users"]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    REROUTED_FIELD_NUMBER: _ClassVar[int]
    USERS_FIELD_NUMBER: _ClassVar[int]
    request_status: RequestStatus
    rerouted: str
    users: _containers.RepeatedCompositeFieldContainer[User]
    def __init__(self, users: _Optional[_Iterable[_Union[User, _Mapping]]] = ..., request_status: _Optional[_Union[RequestStatus, str]] = ..., rerouted: _Optional[str] = ...) -> None: ...

class RequestStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
