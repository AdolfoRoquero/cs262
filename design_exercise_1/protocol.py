# Request type encoded in 3 digit [0-999]
HDR_REQUEST_TYPE_SZ = 3
# 1 : Login Client Request
# 2 : Sign Up Client Request
# 3 : Message Client Request
# 4 : Message Server Reply 
# 5 : ListAll Client Request 
# 6 : ListAll Server Reply 




#
# LOGIN CLIENT REQUEST PROTOCOL
# HDR_REQUEST_TYPE_SZ(1) + HDR_USERNAME_SZ + USERNAME 
#        3 digit         +      2 digits   +  HDR_USERNAME_SZ [0-99]

#
# SIGN UP CLIENT REQUEST PROTOCOL
# HDR_REQUEST_TYPE_SZ(2) + HDR_USERNAME_SZ + USERNAME 
#        3 digit         +      2 digits   +  [0-99]

#
# MESSAGE CLIENT REQUEST PROTOCOL
# HDR_REQUEST_TYPE_SZ(3) + HDR_USERNAME_SZ + USERNAME + HDR_DESTINATARIES_SZ + DESTINATARIES + HDR_MESSAGE + MESSAGE
#        3 digit         +      2 digits   + [0-99]   +         10 digits    +  [0-999999]   +  3 digits   + [0-999]

#
# MESSAGE SERVER REPLY PROTOCOL
# HDR_REQUEST_TYPE_SZ(4) + HDR_USERNAME_SZ + SENDER_USERNAME +  HDR_MESSAGE + MESSAGE
#        3 digit         +      2 digits   +      [0-99]     +   3 digits   + [0-999]

#
# LISTALL CLIENT REQUEST PROTOCOL
# HDR_REQUEST_TYPE_SZ(5) + HDR_USERNAME_SZ + SENDER_USERNAME
#        3 digit         +      2 digits   +      [0-99]

#
# LISTALL SERVER REPLY PROTOCOL
# HDR_REQUEST_TYPE_SZ(5) + HDR_DESTINATARIES_SZ + DESTINATARIES
#        3 digit         +      10 digits   +      [0-999999999]

# Size of the header that encodes the username size
HDR_USERNAME_SZ = 3
HDR_DESTINATARIES_SZ = 10 
HDR_MESSAGE_SZ = 3
