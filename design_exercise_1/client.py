import socket
import sys
import errno
# TODO read IP from config file
HOST = "10.250.227.245"
PORT = 6000


# Size of the header that encodes the username size
HDR_USERNAME_SZ = 2
# 
HDR_DESTINATARIES_SZ = 10 
HDR_MESSAGE_SZ = 3
HDR_REQUEST_TYPE_SZ = 1
HDR_SZ = HDR_USERNAME_SZ + HDR_MESSAGE_SZ + HDR_REQUEST_TYPE_SZ
# Reply Protocol Definition
HDR_USERNAME_FROM_SZ = 1

def client_setup():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    return client_socket

def receive_message(scket):
  try:
    username_hdr = scket.recv(HDR_USERNAME_SZ)
    
    # Connection Error
    if not (len(username_hdr)):
        return False

    username_length = int(username_hdr.decode('utf-8').strip())
    username = scket.recv(username_length).decode('utf-8').strip()

    message_hdr = scket.recv(HDR_MESSAGE_SZ)
    
    # Connection Error
    if not (len(message_hdr)):
        return False

    message_length = int(message_hdr.decode('utf-8').strip())
    message = scket.recv(message_length).decode('utf-8').strip()
    
    return {
        'username': username, # decoded
        'message': message   # decoded
    }
           
  
  except:
     return False


if __name__ == '__main__':
    client_soc = client_setup()
    username = 'Adolfo'
    busername = username.encode("utf-8")
    username_hdr = f"{len(busername):<{HDR_USERNAME_SZ}}".encode('utf-8')

    msg = "CS 143!!!!"
    bmsg = msg.encode("utf-8")
    message_hdr = f"{len(bmsg):<{HDR_MESSAGE_SZ}}".encode('utf-8')

    dest = "Jacobo"
    bdest = dest.encode("utf-8")
    dest_hdr = f"{len(bdest):<{HDR_DESTINATARIES_SZ}}".encode('utf-8')

    msg_type = 'R' # 'r'
    bmsg_type = msg_type.encode("utf-8")

    sent = client_soc.send(username_hdr + busername + 
                           dest_hdr + bdest +
                           message_hdr + bmsg + 
                           bmsg_type)
    
    print('Message sent, %d/%d bytes transmitted' % (sent, len(msg)))


    try:
        while True:
            content = receive_message(client_soc)
            print(f'Message received from user: {content["username"]}')
            print(content["message"])


    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print(f'Reading Error {e}')
            sys.exit()
    except Exception as e:
        print(f'Reading error: {e}')
        sys.exit()

            

    client_soc.close()

