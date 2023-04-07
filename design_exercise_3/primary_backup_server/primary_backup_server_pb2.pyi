from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Message(_message.Message):
    __slots__ = ["date", "destinataries", "sender", "text"]
    DATE_FIELD_NUMBER: _ClassVar[int]
    DESTINATARIES_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    date: _timestamp_pb2.Timestamp
    destinataries: _containers.RepeatedCompositeFieldContainer[User]
    sender: User
    text: str
    def __init__(self, sender: _Optional[_Union[User, _Mapping]] = ..., destinataries: _Optional[_Iterable[_Union[User, _Mapping]]] = ..., text: _Optional[str] = ..., date: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class RequestReply(_message.Message):
    __slots__ = ["reply", "request_status"]
    REPLY_FIELD_NUMBER: _ClassVar[int]
    REQUEST_STATUS_FIELD_NUMBER: _ClassVar[int]
    reply: str
    request_status: int
    def __init__(self, reply: _Optional[str] = ..., request_status: _Optional[int] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...
