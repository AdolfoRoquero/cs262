from datetime import datetime as dt
from time import time 
from protocol import *

def unpack_from_header(scket, header_size, decode = True): 
    # Read header 
    hdr = scket.recv(header_size)

    # Connection Error 
    if not len(hdr): 
        return False 

    content_length = int(hdr.decode('utf-8').strip())
    
    content = scket.recv(content_length)
    if decode: 
        return content.decode('utf-8') 
        
    return content 

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
    version = unpack_from_header(scket, VERSION_SZ) 

    if not version: 
        return False 

    # Read message type
    msg_type = unpack_from_header(scket, MSG_TYPE_HDR_SZ) 

    if (not msg_type) or (msg_type not in VALID_MESSAGE_TYPES): 
        return False 

    # Read timestamp
    timestamp = unpack_from_header(scket, TIMESTAMP_SZ) 

    if not timestamp: 
        return False 

    # Read sender name 
    sender_name = unpack_from_header(scket, USERNAME_HDR_SZ) 

    if not sender_name: 
        return False 

    return {'version': version, 
            'message_type': msg_type, 
            'timestamp': timestamp, 
            'sender_name': sender_name}



