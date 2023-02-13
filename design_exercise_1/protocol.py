# -----------------------------------------------------------------------------------
# WIRE PROTOCOL DEFINITION
# -----------------------------------------------------------------------------------

# MESSAGE TYPE FLAGS
CL_SIGNUP = '1'
CL_LOGIN = '2'
CL_LISTALL = '3'
CL_DEL_USER = '4'
CL_SEND_MSG = '5'

SRV_SIGNUP = '21'
SRV_LOGIN = '22'
SRV_LISTALL = '23'
SRV_DEL_USER = '24'
SRV_FORWARD_MSG = '25'
SRV_MSG_FAILURE = '26'

# HEADER SIZES
MSG_TYPE_HDR_SZ = 3
USERNAME_HDR_SZ = 3
DESTINATARIES_HDR_SZ = 10 
MSG_HDR_SZ = 3
TIMESTAMP_SZ = 3
VERSION_SZ = 1

# MESSAGE METADATA
 