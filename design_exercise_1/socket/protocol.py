"""Chat App - Socket Wire Protocol Constants

This script defines the following constants used for the Wire Protocol (WP):
    - WP Version Number
    - WP Message types
    - WP Segment Header Sizes
"""

# -----------------------------------------------------------------------------------
# Wire Protocol Version
# -----------------------------------------------------------------------------------
VERSION = '1.0'

# -----------------------------------------------------------------------------------
# Message Types
# CL_ stands for Client-made Message types
# SRV_ stands for Server-made Message types
# -----------------------------------------------------------------------------------
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

VALID_MESSAGE_TYPES = [CL_SIGNUP, CL_LOGIN, CL_LISTALL, CL_DEL_USER, CL_SEND_MSG,
                       SRV_SIGNUP, SRV_LOGIN, SRV_LISTALL, SRV_DEL_USER,
                       SRV_FORWARD_MSG, SRV_MSG_FAILURE]


# -----------------------------------------------------------------------------------
# Header Sizes (header size for the encoded length of a segment)
# The existing segment types are:
# Message Type segment, Username segment, Destinataries segment, Message segment,
# Timestamp segment, Version segment
# -----------------------------------------------------------------------------------
MSG_TYPE_HDR_SZ = 3
USERNAME_HDR_SZ = 3
DESTINATARIES_HDR_SZ = 10 
MSG_HDR_SZ = 3
TIMESTAMP_HDR_SZ = 3
VERSION_HDR_SZ = 1

# -----------------------------------------------------------------------------------
# Server Reply Statuses
# When returning success or failure, Server provides more information as part of the
# message body. The different Statuses are used to print different error messages
# without having to send the message itself over the wire.
# -----------------------------------------------------------------------------------

FAILURE = '0'
SUCCESS = '1'
USERNAME_TAKEN_FAILURE = '2'  # "Signup failed: username taken."
INVALID_USERNAME_FAILURE = '3' # Login failed: username doesn't exist


SRV_RPLY_TEXT = {
    FAILURE : 'Request Failed',
    SUCCESS : 'Request Succeded',
    USERNAME_TAKEN_FAILURE: 'Username already taken',
    INVALID_USERNAME_FAILURE: "Invalid username" 
}

