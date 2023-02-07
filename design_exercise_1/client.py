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
  try:
    msg_type = scket.recv(HDR_REQUEST_TYPE_SZ).decode('utf-8').strip() 
    print(msg_type)
    if not msg_type:
        print("Error: message type header missing")
        return False
    
    sender_username_hdr = scket.recv(HDR_USERNAME_SZ)
    
    # Connection Error
    if not (len(sender_username_hdr)):
        return False

    sender_username_length = int(sender_username_hdr.decode('utf-8').strip())
    sender_username = scket.recv(sender_username_length).decode('utf-8').strip()

    message_hdr = scket.recv(HDR_MESSAGE_SZ)
    
    # Connection Error
    if not (len(message_hdr)):
        return False

    message_length = int(message_hdr.decode('utf-8').strip())
    message = scket.recv(message_length).decode('utf-8').strip()
    
    return {
        'username': sender_username, # decoded
        'message': message   # decoded
    }
     
  
  except:
     return False


if __name__ == '__main__':
    client_soc = client_setup()
    new_or_existing = input("New or existing user (N or E): ").strip()
    client_msg_type = '1' if new_or_existing == 'E' else ('2' if new_or_existing == 'N' else '-1')
    assert client_msg_type != '-1', "Error in msg type"
    bmsg_type = f"{client_msg_type:<{HDR_REQUEST_TYPE_SZ}}".encode("utf-8")


    username = input("Enter username: ").strip()
    busername = username.encode("utf-8")
    username_hdr = f"{len(busername):<{HDR_USERNAME_SZ}}".encode('utf-8')

    sent = client_soc.send(bmsg_type + 
                           username_hdr + busername)

    while True:
        dest = input(f"{username}> Enter destinatary (comma-separated if multiple): ").strip()
        bdest = dest.encode("utf-8")
        dest_hdr = f"{len(bdest):<{HDR_DESTINATARIES_SZ}}".encode('utf-8')

        msg = input(f"{username}>Enter text: ")
        if msg:
            bmsg = msg.encode("utf-8")
            message_hdr = f"{len(bmsg):<{HDR_MESSAGE_SZ}}".encode('utf-8')
            
            msg_type = '3'
            bmsg_type = f"{msg_type:<{HDR_REQUEST_TYPE_SZ}}".encode("utf-8")
            sent = client_soc.send(bmsg_type + 
                                username_hdr + busername +
                                dest_hdr + bdest +
                                message_hdr + bmsg)
            
            print('Message sent, %d/%d bytes transmitted' % (sent, len(msg)))


        try:
            while True:
                content = receive_message(client_soc)
                if content:
                    print(f'Message received from user: {content["username"]}')
                    print(content["message"])


        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print(f'Reading Error {e}')
                sys.exit()
            continue
        except Exception as e:
            print(f'Reading error: {e}')
            sys.exit()

            

    #client_soc.close()

