import socket
import select

HOST = socket.gethostname()#'65.112.8.28'
print(HOST)
PORT = 6000
TIMEOUT = 60 # In seconds

# Request Protocol Definition
# HEADER:
# USERNAME_LENGTH -->  16 byte
# MESSAGE_LENGTH -->  150 byte
# TYPE_REQUEST --> 1 byte
# DATA:
# USERNAME --> 
# MESSAGE -->

# Size of the header that encodes the username size
HDR_USERNAME_SZ = 2
# 
HDR_DESTINATARIES_SZ = 10 
HDR_MESSAGE_SZ = 3
HDR_REQUEST_TYPE_SZ = 1
HDR_SZ = HDR_USERNAME_SZ + HDR_MESSAGE_SZ + HDR_REQUEST_TYPE_SZ


# Reply Protocol Definition
HDR_USERNAME_FROM_SZ = 1


# Stores existing usernames 
# Usernames have a length from 1 to 99 chars
usernames = ['adolfo', 
             'le', 
             'jacobo']

# Key: socket, val: {username: , addr:}
clients = {}

def server_setup():
 server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 server_socket.bind((HOST, PORT))
 server_socket.listen()
 return server_socket



def receive_message(scket):
  try:
    username_hdr = scket.recv(HDR_USERNAME_SZ)
    
    # Connection Error
    if not (len(username_hdr)):
        return False

    username_length = int(username_hdr.decode('utf-8').strip())
    username = scket.recv(username_length).decode('utf-8').strip()


    destinataries_hdr = scket.recv(HDR_DESTINATARIES_SZ)
    # Connection Error
    if not (len(destinataries_hdr)):
        return False

    destinataries_length = int(destinataries_hdr.decode('utf-8').strip())
    destinataries = scket.recv(destinataries_length).decode('utf-8').strip().split(',')


    message_hdr = scket.recv(HDR_MESSAGE_SZ)
    
    # Connection Error
    if not (len(message_hdr)):
        return False

    message_length = int(message_hdr.decode('utf-8').strip())
    message = scket.recv(message_length)

    # TODO Deal with request type
    request_type = scket.recv(HDR_REQUEST_TYPE_SZ).decode('utf-8').strip()
    
    if not (len(request_type)):
        return False
    
    return {'username_hdr': username_hdr,
            'username': username, # decoded
            'message_hdr': message_hdr,
            'message': message,   # encoded
            'request_type': request_type,  # decoded
            'destinataries': destinataries} # decoded and converted to list
  
  except:
     return False

if __name__ == '__main__':
 server_socket = server_setup()
 socket_list = [server_socket]

 while True:
    ready_to_read, ready_to_write, in_error = select.select(
                    socket_list,
                    socket_list,
                    [],
                    TIMEOUT)
  
    for sockt in ready_to_read:

        # Accept new connections for server socket
        if sockt == server_socket:
            # Create new socket for send/receive from client
            conn, addr = server_socket.accept()

            message_content = receive_message(sockt)

            # Add new socket to the list of sockets passed to select
            socket_list.append(conn)

            clients[conn] = {'username' : message_content['username'],
                             'addr': addr}

            print(f"Accepted new connection from user: {message_content['username']} at {addr[0]}:{addr[1]}")

        else:
            message_content = receive_message(sockt)
            if not message_content:
                print(f"Closed connection from user: {clients[sockt]['username']} at {clients[sockt]['addr'][0]}:{clients[sockt]['addr'][1]}")
                socket_list.remove(sockt)
                del clients[sockt] 
                continue

            for sockt, info in clients.items():
               if info['username'] in message_content['destinataries']:
                  sockt.send(
                     message_content['username_hdr'] + 
                     message_content['username'].encode('utf-8') + 
                     message_content['message_hdr'] + 
                     message_content['message'])
                  
               
               
               






