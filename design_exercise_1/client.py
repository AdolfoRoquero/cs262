import socket
import sys
import errno
from protocol import *

# TODO read IP from config file
HOST = "10.250.227.245"
PORT = 6000


def client_setup():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    client_socket.setblocking(False)
    return client_socket

def receive_message(scket):
    msg_type = scket.recv(MSG_TYPE_HDR_SZ).decode('utf-8').strip() 
    if not msg_type:
        print("Error: message type header missing")
        return False

    message_content = {'message_type': msg_type}
    if msg_type == SRV_LISTALL: 
        message_length = int(scket.recv(DESTINATARIES_HDR_SZ).decode('utf-8').strip())
        message = scket.recv(message_length).decode('utf-8').split(',')
        message_content['message'] = message
        return message_content
    
    elif msg_type == SRV_DEL_USER:
        message_length = int(scket.recv(MSG_HDR_SZ).decode('utf-8').strip())
        message = scket.recv(message_length).decode('utf-8')
        message_content['message'] = message
        return message_content
    
    else: 
        sender_username_hdr = scket.recv(USERNAME_HDR_SZ)
        
        # Connection Error
        if not (len(sender_username_hdr)):
            return False

        sender_username_length = int(sender_username_hdr.decode('utf-8').strip())
        sender_username = scket.recv(sender_username_length).decode('utf-8').strip()

        message_hdr = scket.recv(MSG_HDR_SZ)
        
        # Connection Error
        if not (len(message_hdr)):
            return False

        message_length = int(message_hdr.decode('utf-8').strip())
        message = scket.recv(message_length).decode('utf-8').strip()
        
        message_content['username'] = sender_username
        message_content['message'] = message
        return message_content
     


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

    bmsg_type = f"{client_msg_type:<{MSG_TYPE_HDR_SZ}}".encode("utf-8")


    username = input("Enter username: ").strip()
    busername = username.encode("utf-8")
    username_hdr = f"{len(busername):<{USERNAME_HDR_SZ}}".encode('utf-8')

    sent = client_socket.send(bmsg_type + 
                           username_hdr + busername)

    print("to send messages, use format destinaries (comma separated); message")

    while True:
        # wait for message 
        dest = input(f"{username}> Destinataries: ").strip()

        if dest.startswith("listall"):
            msg_type = CL_LISTALL
            bmsg_type = f"{msg_type:<{MSG_TYPE_HDR_SZ}}".encode("utf-8")

            username_filter = dest.replace('listall', '').strip()
            busername_filter = username_filter.encode('utf-8')
            username_filter_hdr = f"{len(busername_filter):<{MSG_HDR_SZ}}".encode("utf-8")

            sent = client_socket.send(bmsg_type + username_hdr + busername + 
                                      username_filter_hdr + busername_filter)
            print('Listall request sent, %d bytes transmitted' % (sent))
        
        elif dest == "delete_user":
            msg_type = CL_DEL_USER
            bmsg_type = f"{msg_type:<{MSG_TYPE_HDR_SZ}}".encode("utf-8")
            sent = client_socket.send(bmsg_type + username_hdr + busername)
            print('Delete user request sent, %d bytes transmitted' % (sent))
    
        elif dest:
            msg = input(f"{username}> Message: ").strip()
            if msg:
                bdest = dest.encode("utf-8")
                dest_hdr = f"{len(bdest):<{DESTINATARIES_HDR_SZ}}".encode('utf-8')
                bmsg = msg.encode("utf-8")
                message_hdr = f"{len(bmsg):<{MSG_HDR_SZ}}".encode('utf-8')
                
                msg_type = CL_SEND_MSG
                bmsg_type = f"{msg_type:<{MSG_TYPE_HDR_SZ}}".encode("utf-8")
                sent = client_socket.send(bmsg_type + 
                                    username_hdr + busername +
                                    dest_hdr + bdest +
                                    message_hdr + bmsg)
                
                print('Message sent, %d/%d bytes transmitted' % (sent, len(msg)))


        try:
            while True:
                content = receive_message(client_socket)
                if content:
                    if content['message_type'] == SRV_LISTALL: 
                        print(f'{username} > {",".join(content["message"])}')
                    elif content['message_type'] == SRV_DEL_USER:
                        if content['message'] == "Success":
                            print(f"User {username} deleted. Closing Connection")
                            client_socket.close()
                            sys.exit()
                    else: 
                        print(f'{content["username"]} > {content["message"]}')


        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print(f'E1 Reading Error {e}')
                sys.exit()

            continue
        except Exception as e:
            print(f'E2 Reading error: {e}')
            sys.exit()

            

    #client_soc.close()

