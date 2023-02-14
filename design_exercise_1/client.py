import socket
import sys
import errno
from protocol import *
from utils import * 
import traceback

# TODO read IP from config file
HOST = "10.250.227.245"
PORT = 6000


def client_setup():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    client_socket.setblocking(False)
    return client_socket

def receive_message(scket):

    # Read metadata 
    metadata = read_metadata_header(scket)

    if not metadata: 
        return False 

    message = {'metadata': metadata}

    if message['metadata']['message_type'] == SRV_LISTALL: 
        # Read destinataries 
        message_content_str = unpack_from_header(scket, DESTINATARIES_HDR_SZ)

        if not message_content_str: 
            return False
        
        message['message_content'] = message_content_str.split(',')
        return message

    elif message['metadata']['message_type'] in [SRV_DEL_USER, SRV_MSG_FAILURE]:
        message_content = unpack_from_header(scket, MSG_HDR_SZ)
        if not message_content: 
            return False 
        message['message_content'] = message_content
        return message

    elif message['metadata']['message_type'] == SRV_FORWARD_MSG: 
        sender_username =  unpack_from_header(scket, USERNAME_HDR_SZ)
        if not sender_username: 
            return False
        
        sender_timestamp = unpack_from_header(scket, TIMESTAMP_SZ)

        if not sender_timestamp: 
            return False

        message_hdr = scket.recv(MSG_HDR_SZ)
        
        # Connection Error
        if not (len(message_hdr)):
            return False

        message_length = int(message_hdr.decode('utf-8').strip())
        message_content = scket.recv(message_length).decode('utf-8').strip()
        
        message['sender_timestamp'] = sender_timestamp
        message['sender_username'] = sender_username
        message['message_content'] = message_content
        return message


if __name__ == '__main__':
    client_socket = client_setup()
    while True:
        new_or_existing = input("New or existing user (N or E): ").strip()
        if new_or_existing == 'E':
            client_msg_type = CL_LOGIN  
            break
        elif new_or_existing == 'N':
            client_msg_type = CL_SIGNUP
            break

    username = input("Enter username: ").strip()
    metadata_hdr = create_metadata_header(client_msg_type, username)

    sent = client_socket.send(metadata_hdr)
    
    print("to send messages, use format destinaries (comma separated); message")

    while True:
        # wait for message 
        dest = input(f"{username}> Destinataries: ").strip()

        if dest.startswith("listall"):
            metadata_hdr = create_metadata_header(CL_LISTALL, username)

            username_filter = dest.replace('listall', '').strip()
            busername_filter = username_filter.encode('utf-8')
            username_filter_hdr = f"{len(busername_filter):<{MSG_HDR_SZ}}".encode("utf-8")

            sent = client_socket.send(metadata_hdr + username_filter_hdr + busername_filter)
            print('Listall request sent, %d bytes transmitted' % (sent))
        
        elif dest == "delete_user":
            metadata_hdr = create_metadata_header(CL_DEL_USER, username)
            sent = client_socket.send(metadata_hdr)
            print('Delete user request sent, %d bytes transmitted' % (sent))
    
        elif dest:
            msg = input(f"{username}> Message: ").strip()
            if msg:
                metadata_hdr = create_metadata_header(CL_SEND_MSG, username)
                bdest = dest.encode("utf-8")
                dest_hdr = f"{len(bdest):<{DESTINATARIES_HDR_SZ}}".encode('utf-8')
                bmsg = msg.encode("utf-8")
                message_hdr = f"{len(bmsg):<{MSG_HDR_SZ}}".encode('utf-8')
                sent = client_socket.send(metadata_hdr +
                                    dest_hdr + bdest +
                                    message_hdr + bmsg)
                
                print('Message sent, %d/%d bytes transmitted' % (sent, len(msg)))


        try:
            while True:
                message = receive_message(client_socket)
                if message:
                    if message['metadata']['message_type'] == SRV_LISTALL: 
                        print(f'{username} > {",".join(message["message_content"])}')
                    elif message['metadata']['message_type'] == SRV_DEL_USER:
                        if message['message_content'] == "Success":
                            print(f"User {username} deleted. Closing Connection")
                            client_socket.close()
                            sys.exit()
                    elif message['metadata']['message_type'] == SRV_MSG_FAILURE:
                        print(f"Server Error: {message['message_content']}\nClosing Connection")
                        client_socket.close()
                        sys.exit()
                    
                    else: 
                        print(f'{message["sender_username"], message["sender_timestamp"]} > {message["message_content"]}')


        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print(f'E1 Reading Error {e}')
                sys.exit()

            continue
        except Exception as e:
            print(traceback.format_exc())
            print(f'E2 Reading error: {e}')
            sys.exit()

            

    #client_soc.close()

