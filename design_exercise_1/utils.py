from datetime import datetime as dt
from time import time 
from protocol import *


def encode_message_segment(content = None, header_size = None):
    """Takes a text to be encoded and the number of bytes used for the encoding header
        for this type of message. Encodes the text and store the size of the encoded 
        message in header.

        Parameters
        ----------
        content (str): The message to be encoded 
        header_size (int): The size of the header for this type of message 

        Returns 
        -------
        str: binary string with encoded header and content 

        Raises
        ------
        ValueError: If either parameters are left empty or header_size type is incorrect  
    """
    if not header_size or not isinstance(header_size, int): 
        raise ValueError("Invalid argument for function")
    
    bcontent = content.encode('utf-8')
    content_hdr = f"{len(bcontent):<{header_size}}".encode('utf-8')
    return content_hdr + bcontent


def unpack_from_header(scket, header_size, decode = True): 
    """Takes a socket and a header size (in bytes) and reads header from the socket, 
       then reads the message of length specified in the header. Option to decode or 
       not the message content. 

        Parameters
        ----------
        scket (socket): The socket to read from
        header_size (int): The size of the header for this type of message 
        decode (bool), optional: Flag to decode or not the message read from socket. 

        Returns 
        -------
        str: binary string with encoded message or string with decoded message

        TODO Raises
        ------
        ValueError: If either parameters are left empty or header_size type is incorrect  
    """
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
    """Takes a message type and the name of sender and returns the encoded metadata for the 
        message to be sent. 

        Parameters
        ----------
        msg_type (str): The type of message, as defined in protocol or .proto file.
        sender__name (str): Identifier for who sent the message. 

        Returns 
        -------
        str: binary string with encoded metadata
    """

    # version 
    version_enc = encode_message_segment(VERSION, VERSION_SZ)
    # message type
    msg_type_enc = encode_message_segment(msg_type, MSG_TYPE_HDR_SZ)

    # timestamp 
    timestamp = dt.now().strftime("%d/%m/%Y, %H:%M:%S")
    timestamp_enc = encode_message_segment(timestamp, TIMESTAMP_SZ)

    # sender name
    sender_enc = encode_message_segment(sender_name, USERNAME_HDR_SZ)

    return version_enc + msg_type_enc + timestamp_enc + sender_enc


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



