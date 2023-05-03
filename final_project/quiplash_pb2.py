# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: quiplash.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0equiplash.proto\x12\x07\x63hatapp\x1a\x1fgoogle/protobuf/timestamp.proto\"\x80\x01\n\x0cRequestReply\x12\x12\n\x05reply\x18\x01 \x01(\tH\x00\x88\x01\x01\x12.\n\x0erequest_status\x18\x02 \x01(\x0e\x32\x16.chatapp.RequestStatus\x12\x15\n\x08rerouted\x18\x03 \x01(\tH\x01\x88\x01\x01\x42\x08\n\x06_replyB\x0b\n\t_rerouted\"\x8d\x01\n\rJoinGameReply\x12\x18\n\x0bnum_players\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12.\n\x0erequest_status\x18\x02 \x01(\x0e\x32\x16.chatapp.RequestStatus\x12\x15\n\x08rerouted\x18\x03 \x01(\tH\x01\x88\x01\x01\x42\x0e\n\x0c_num_playersB\x0b\n\t_rerouted\"\\\n\x04User\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x17\n\nip_address\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x11\n\x04port\x18\x03 \x01(\tH\x01\x88\x01\x01\x42\r\n\x0b_ip_addressB\x07\n\x05_port\"E\n\x08Question\x12\x13\n\x0bquestion_id\x18\x01 \x01(\t\x12\x15\n\rquestion_text\x18\x02 \x01(\t\x12\r\n\x05topic\x18\x03 \x01(\t\"8\n\x0cQuestionList\x12(\n\rquestion_list\x18\x01 \x03(\x0b\x32\x11.chatapp.Question\"U\n\x06\x41nswer\x12!\n\nrespondent\x18\x01 \x01(\x0b\x32\r.chatapp.User\x12\x13\n\x0b\x61nswer_text\x18\x02 \x01(\t\x12\x13\n\x0bquestion_id\x18\x03 \x01(\t\"2\n\nAnswerList\x12$\n\x0b\x61nswer_list\x18\x01 \x03(\x0b\x32\x0f.chatapp.Answer\"W\n\x04Vote\x12\x1c\n\x05voter\x18\x01 \x01(\x0b\x32\r.chatapp.User\x12\x13\n\x0bquestion_id\x18\x02 \x01(\t\x12\x1c\n\x05votee\x18\x03 \x01(\x0b\x32\r.chatapp.User\"\xc7\x01\n\x10GameNotification\x12\x38\n\x04type\x18\x01 \x01(\x0e\x32*.chatapp.GameNotification.NotificationType\x12\x11\n\x04text\x18\x02 \x01(\tH\x00\x88\x01\x01\"]\n\x10NotificationType\x12\x0e\n\nGAME_START\x10\x00\x12\x10\n\x0cVOTING_START\x10\x01\x12\x11\n\rSCORING_START\x10\x02\x12\x14\n\x10QUESTION_TIMEOUT\x10\x03\x42\x07\n\x05_text\"\x11\n\x0fLivenessRequest\"\"\n\x10LivenessResponse\x12\x0e\n\x06status\x18\x01 \x01(\t*6\n\rRequestStatus\x12\x0b\n\x07SUCCESS\x10\x00\x12\n\n\x06\x46\x41ILED\x10\x01\x12\x0c\n\x08REROUTED\x10\x02\x32\xe5\x02\n\x08Quiplash\x12\x31\n\x08JoinGame\x12\r.chatapp.User\x1a\x16.chatapp.JoinGameReply\x12=\n\rSendQuestions\x12\x15.chatapp.QuestionList\x1a\x15.chatapp.RequestReply\x12\x34\n\nSendAnswer\x12\x0f.chatapp.Answer\x1a\x15.chatapp.RequestReply\x12\x30\n\x08SendVote\x12\r.chatapp.Vote\x1a\x15.chatapp.RequestReply\x12<\n\x0eSendAllAnswers\x12\x13.chatapp.AnswerList\x1a\x15.chatapp.RequestReply\x12\x41\n\rNotifyPlayers\x12\x19.chatapp.GameNotification\x1a\x15.chatapp.RequestReplyB0\n\x18io.grpc.examples.chatAPPB\x0c\x43hatAppProtoP\x01\xa2\x02\x03\x43\x41Pb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'quiplash_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\030io.grpc.examples.chatAPPB\014ChatAppProtoP\001\242\002\003CAP'
  _REQUESTSTATUS._serialized_start=1043
  _REQUESTSTATUS._serialized_end=1097
  _REQUESTREPLY._serialized_start=61
  _REQUESTREPLY._serialized_end=189
  _JOINGAMEREPLY._serialized_start=192
  _JOINGAMEREPLY._serialized_end=333
  _USER._serialized_start=335
  _USER._serialized_end=427
  _QUESTION._serialized_start=429
  _QUESTION._serialized_end=498
  _QUESTIONLIST._serialized_start=500
  _QUESTIONLIST._serialized_end=556
  _ANSWER._serialized_start=558
  _ANSWER._serialized_end=643
  _ANSWERLIST._serialized_start=645
  _ANSWERLIST._serialized_end=695
  _VOTE._serialized_start=697
  _VOTE._serialized_end=784
  _GAMENOTIFICATION._serialized_start=787
  _GAMENOTIFICATION._serialized_end=986
  _GAMENOTIFICATION_NOTIFICATIONTYPE._serialized_start=884
  _GAMENOTIFICATION_NOTIFICATIONTYPE._serialized_end=977
  _LIVENESSREQUEST._serialized_start=988
  _LIVENESSREQUEST._serialized_end=1005
  _LIVENESSRESPONSE._serialized_start=1007
  _LIVENESSRESPONSE._serialized_end=1041
  _QUIPLASH._serialized_start=1100
  _QUIPLASH._serialized_end=1457
# @@protoc_insertion_point(module_scope)
