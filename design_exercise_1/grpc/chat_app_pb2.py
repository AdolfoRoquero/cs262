# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chat_app.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x63hat_app.proto\x12\x07\x63hatapp\x1a\x1fgoogle/protobuf/timestamp.proto\"\x18\n\x04User\x12\x10\n\x08username\x18\x01 \x01(\t\"\x1d\n\x0crequestReply\x12\r\n\x05reply\x18\x01 \x01(\t\"(\n\x08UserList\x12\x1c\n\x05users\x18\x01 \x03(\x0b\x32\r.chatapp.User\"\x8e\x01\n\x0b\x43hatMessage\x12\x1d\n\x06sender\x18\x01 \x01(\x0b\x32\r.chatapp.User\x12(\n\rdestinataries\x18\x02 \x01(\x0b\x32\x11.chatapp.UserList\x12\x0c\n\x04text\x18\x03 \x01(\t\x12(\n\x04\x64\x61te\x18\x04 \x01(\x0b\x32\x1a.google.protobuf.Timestamp2\xc8\x02\n\x07\x43hatApp\x12/\n\x05Login\x12\r.chatapp.User\x1a\x15.chatapp.requestReply\"\x00\x12\x30\n\x06SignUp\x12\r.chatapp.User\x1a\x15.chatapp.requestReply\"\x00\x12-\n\x07ListAll\x12\r.chatapp.User\x1a\x11.chatapp.UserList\"\x00\x12\x34\n\nDeleteUser\x12\r.chatapp.User\x1a\x15.chatapp.requestReply\"\x00\x12<\n\x0bSendMessage\x12\x14.chatapp.ChatMessage\x1a\x15.chatapp.requestReply\"\x00\x12\x37\n\x0eReceiveMessage\x12\r.chatapp.User\x1a\x14.chatapp.ChatMessage\"\x00\x42\x30\n\x18io.grpc.examples.chatAPPB\x0c\x43hatAppProtoP\x01\xa2\x02\x03\x43\x41Pb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_app_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\030io.grpc.examples.chatAPPB\014ChatAppProtoP\001\242\002\003CAP'
  _USER._serialized_start=60
  _USER._serialized_end=84
  _REQUESTREPLY._serialized_start=86
  _REQUESTREPLY._serialized_end=115
  _USERLIST._serialized_start=117
  _USERLIST._serialized_end=157
  _CHATMESSAGE._serialized_start=160
  _CHATMESSAGE._serialized_end=302
  _CHATAPP._serialized_start=305
  _CHATAPP._serialized_end=633
# @@protoc_insertion_point(module_scope)
