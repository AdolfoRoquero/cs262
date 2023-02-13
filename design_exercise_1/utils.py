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

def read_metadata_header(scket): 

    # Read version 
    version_hdr = scket.recv(VERSION_SZ)

    # Connection Error 
    if not len(version_hdr): 
        return False 
    version_length = int(version_hdr.decode('utf-8').strip())
    version = scket.recv(version_length).decode('utf-8') 

    # Read message type
    msg_type_hdr = scket.recv(MSG_TYPE_HDR_SZ)

    # Connection Error 
    if not len(msg_type_hdr): 
        return False 

    msg_type_length = int(msg_type_hdr.decode('utf-8').strip())
    msg_type = scket.recv(msg_type_length).decode('utf-8') 

    if msg_type not in VALID_MESSAGE_TYPES: 
        return False 


        # Read timestamp
    timestamp_hdr = scket.recv(TIMESTAMP_SZ)

    # Connection Error 
    if not len(timestamp_hdr): 
        return False 

    timestamp_length = int(timestamp_hdr.decode('utf-8').strip())
    timestamp = scket.recv(timestamp_length).decode('utf-8') 

    # Read sender name 
    sender_name_hdr = scket.recv(USERNAME_HDR_SZ)

    # Connection Error 
    if not len(sender_name_hdr): 
        return False 

    sender_name_length = int(sender_name_hdr.decode('utf-8').strip())
    sender_name = scket.recv(sender_name_length).decode('utf-8') 

    return {'version': version, 
            'message_type': msg_type, 
            'timestamp': timestamp, 
            'sender_name': sender_name}



