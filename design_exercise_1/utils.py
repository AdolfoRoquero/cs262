from datetime import datetime as dt 
from protocol import *
import socket


def create_metadata_header(msg_type, sender_name): 

    # version 
    bversion = VERSION.encode('utf-8')
    version_hdr = f"{len(bversion):<{VERSION_SZ}}".encode('utf-8')

    # message type  
    bmsg_type = msg_type.encode('utf-8')
    msg_type_hdr = f"{len(bmsg_type):<{MSG_TYPE_HDR_SZ}}".encode('utf-8')

    # timestamp 
    timestamp = dt.now().strftime("%d/%m/%Y, %H:%M:%S")
    btimestamp = timestamp.encode('utf-8')
    timestamp_hdr = f"{len(btimestamp):<{TIMESTAMP_SZ}}".encode('utf-8')

    # sender name
    bsender_name = sender_name.encode('utf-8')
    bsender_hdr = f"{len(bsender_name):<{USERNAME_HDR_SZ}}".encode('utf-8')

    return (version_hdr + bversion + 
            msg_type_hdr + bmsg_type + 
            timestamp_hdr + btimestamp + 
            bsender_hdr + bsender_name)

def read_metadata_header(socket): 
    try:
        # Read version 
        version_hdr = int(socket.recv(VERSION_SZ).decode('utf-8').strip())
        # Connection Error 
        if not len(version_hdr): 
            raise Exception("Metadata version header missing")
        version = socket.recv(version_hdr).decode('utf-8') 

        # Read message type
        msg_type_hdr = socket.recv(MSG_TYPE_HDR_SZ)

        # Connection Error 
        if not len(msg_type_hdr): 
            raise Exception("Metadata message type header missing")

        msg_type = socket.recv(msg_type_hdr).decode('utf-8') 

        if msg_type not in VALID_MESSAGE_TYPES: 
            raise Exception("Unrecognized message type")

         # Read timestamp
        timestamp_hdr = int(socket.recv(TIMESTAMP_SZ).decode('utf-8').strip())

        # Connection Error 
        if not len(timestamp_hdr): 
            raise Exception("Metadata timestamp header missing")

        timestamp = socket.recv(timestamp_hdr).decode('utf-8') 

        # Read sender name 
        sender_name_hdr = int(socket.recv(USERNAME_HDR_SZ).decode('utf-8').strip())

        # Connection Error 
        if not len(sender_name_hdr): 
            raise Exception("Metadata sender name header missing")

        sender_name = socket.recv(sender_name_hdr).decode('utf-8') 

        return {'version': version, 
                'message_type': msg_type, 
                'timestamp': timestamp, 
                'sender_name': sender_name}

    except Exception as e:
        print(e)
        return False
