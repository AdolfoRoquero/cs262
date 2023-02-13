# -----------------------------------------------------------------------------------
# WIRE PROTOCOL DEFINITION
# -----------------------------------------------------------------------------------

# VERSION
VERSION = '1.0'

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

VALID_MESSAGE_TYPES = [CL_SIGNUP,CL_LOGIN,CL_LISTALL,CL_DEL_USER,CL_SEND_MSG,
                       SRV_SIGNUP ,SRV_LOGIN ,SRV_LISTALL ,SRV_DEL_USER ,
                       SRV_FORWARD_MSG ,SRV_MSG_FAILURE]

# HEADER SIZES
MSG_TYPE_HDR_SZ = 3
USERNAME_HDR_SZ = 3
DESTINATARIES_HDR_SZ = 10 
MSG_HDR_SZ = 3
TIMESTAMP_SZ = 3
VERSION_SZ = 1

# MESSAGE METADATA
