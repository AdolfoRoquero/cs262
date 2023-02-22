"""Chat App - Socket Wire Protocol Helper Functions

This script defines helper functions for encoding and decoding messages
according to be used when implementing a Wire Protocol.

This file can be imported as a module and contains the following
functions:
    - encode_message_segment(content, header_size)
    - unpack_message_segment(scket, header_size, decode)
    - create_metadata_header(msg_type, sender_name)
    - read_metadata_header(scket)

"""

from datetime import datetime as dt
from protocol import *


def encode_message_segment(content = None, header_size = None):
    """
    Encodes text and stores the size of the encoded message in header.
    Takes the text to be encoded and the number of bytes used for the encoding of the header. 

    Parameters
    ----------
        content : str
            The text to be encoded
        header_size : int 
            The size of the header (the header encodes the size of the encoded text itself) 

    Returns 
    -------
        str: The binary string of the concatenated encoded header and encoded content 

    Raises
    ------
        ValueError: If either parameters are left empty or header_size type is incorrect  
    """
    if not header_size or not isinstance(header_size, int): 
        raise ValueError("Invalid argument for function")
    
    bcontent = content.encode('utf-8')
    content_hdr = f"{len(bcontent):<{header_size}}".encode('utf-8')
    return content_hdr + bcontent


def unpack_message_segment(scket, header_size, decode = True): 
    """
    Given a header size, reads the header, decodes the header to get the length 
    of the encoded segment, then reads and decodes (depending on flag) the segment.
    Option to decode or not the message content. 
    This function is the reverse of encode_message_segment().
    
    Parameters
    ----------
        skcet : socket.Socket
            The socket to read the message segment from.
        header_size : int
            The size of the header for this type of message.
        decode (optional) : bool
            Boolean flag that indicates whether to decode the message or not the message. 

    Returns 
    -------
        str: string of the message (encoded or not depending on the flag).

    # TODO
    Raises
    ------
    ValueError: If either parameters are left empty or header_size type is incorrect 
    """
    # Read as many bites as specified by the Wire Protocol header_size 
    hdr = scket.recv(header_size)

    # Connection Error 
    if not len(hdr): 
        return False 

    # Decode the header of the segment which contains the lenght of the encoding of the segment.
    content_length = int(hdr.decode('utf-8').strip())

    content = scket.recv(content_length)
    if decode: 
        return content.decode('utf-8') 
        
    return content 

def create_metadata_header(msg_type, sender_name): 
    """
    Builds encoded metadata header for a message sent by a user.

    Parameters
    ----------
        msg_type : str
            The type of message, as defined in the wire protocol (protocol.py file).
        sender_name : str 
            Username of the message sender. 

    Returns 
    -------
        str: encoded binary string of the metadata (Protocol version, message type, timestamp, sender)
    """

    # Encoding of the Wire protocol version. 
    version_enc = encode_message_segment(VERSION, VERSION_HDR_SZ)

    # Encoding of the Wire protocol message type.
    msg_type_enc = encode_message_segment(msg_type, MSG_TYPE_HDR_SZ)

    # Encoding of the timestamp at which the message is sent.
    timestamp = dt.now().strftime("%d/%m/%Y, %H:%M:%S")
    timestamp_enc = encode_message_segment(timestamp, TIMESTAMP_HDR_SZ)

    # Encoding of the sender username.
    sender_enc = encode_message_segment(sender_name, USERNAME_HDR_SZ)

    # Return concatenated encoded string of all the metadata segments.
    return version_enc + msg_type_enc + timestamp_enc + sender_enc


def read_metadata_header(scket): 
    """
    Reads metadata from a given socket and decodes it.
    This function is the reverse of create_metadata_header().

    Parameters
    ----------
        skcet : socket.Socket
            The socket to read the metadata header from.
    Returns 
    -------
        dict : {version: str, message_type: str, timestamp: str, sender_name: str}
        Dictionary with metadata attributes as keys
    """

    # Decoded Wire protocol version.
    version = unpack_message_segment(scket, VERSION_HDR_SZ) 

    if not version: 
        return False 

    # Decoded the Wire protocol message type
    msg_type = unpack_message_segment(scket, MSG_TYPE_HDR_SZ) 

    if (not msg_type) or (msg_type not in VALID_MESSAGE_TYPES): 
        return False 

    # Decoded timestamp at which the message is sent.
    timestamp = unpack_message_segment(scket, TIMESTAMP_HDR_SZ) 

    if not timestamp: 
        return False 

    # Decoded the sender username.
    sender_name = unpack_message_segment(scket, USERNAME_HDR_SZ) 

    if not sender_name: 
        return False 

    return {'version': version, 
            'message_type': msg_type, 
            'timestamp': timestamp, 
            'sender_name': sender_name}



