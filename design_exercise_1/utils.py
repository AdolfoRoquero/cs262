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
        version_hdr = socket.recv(VERSION_SZ)

        # Connection Error 
        if not len(version_hdr): 
            print("version")
            # raise Exception("Metadata version header missing")
        version_length = int(version_hdr.decode('utf-8').strip())
        version = socket.recv(version_length).decode('utf-8') 

        # Read message type
        msg_type_hdr = socket.recv(MSG_TYPE_HDR_SZ)

        # Connection Error 
        if not len(msg_type_hdr): 
            print("type")
            # raise Exception("Metadata message type header missing")

        msg_type_length = int(msg_type_hdr.decode('utf-8').strip())
        msg_type = socket.recv(msg_type_length).decode('utf-8') 
        print(msg_type)

        if msg_type not in VALID_MESSAGE_TYPES: 
            print("type check")

            # raise Exception("Unrecognized message type")

         # Read timestamp
        timestamp_hdr = socket.recv(TIMESTAMP_SZ)

        # Connection Error 
        if not len(timestamp_hdr): 
            print("timestamp")
            # raise Exception("Metadata timestamp header missing")
        timestamp_length = int(timestamp_hdr.decode('utf-8').strip())
        timestamp = socket.recv(timestamp_length).decode('utf-8') 
        print(timestamp)

        # Read sender name 
        sender_name_hdr = socket.recv(USERNAME_HDR_SZ)

        # Connection Error 
        if not len(sender_name_hdr): 
            print("sender name")
            # raise Exception("Metadata sender name header missing")

        sender_name_length = int(sender_name_hdr.decode('utf-8').strip())
        sender_name = socket.recv(sender_name_length).decode('utf-8') 
        print(sender_name)

        return {'version': version, 
                'message_type': msg_type, 
                'timestamp': timestamp, 
                'sender_name': sender_name}

    except Exception as e:
        print(e)
        return False
