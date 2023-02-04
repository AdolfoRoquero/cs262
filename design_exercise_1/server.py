import socket
import select

HOST = socket.gethostname()#'65.112.8.28'
print(HOST)
PORT = 6000
TIMEOUT = 60 # In seconds

# Protocol Definition

# HEADER:
# USERNAME_LENGTH -->  16 byte
# MESSAGE_LENGTH -->  150 byte
# TYPE_REQUEST --> 1 byte
# DATA:
# USERNAME --> 
# MESSAGE -->
HDR_USERNAME_SZ = 16
HDR_MESSAGE_SZ = 150
HDR_REQUEST_TYPE_SZ = 1
HDR_SZ = HDR_USERNAME_SZ + HDR_MESSAGE_SZ + HDR_REQUEST_TYPE_SZ

# Stores existing usernames
usernames = []

# Key: socket, val: username
clients = {}

def server_setup():
 server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
 server_socket.bind((HOST, PORT))
 server_socket.listen()
 return server_socket





def receive_message(socket):
  socket.recv()
  
  

 




def server_():
 client_socket, addr = server_socket.accept()
 print('Connected to by:', addr)

 bdata = client_socket.recv(128)
 data = bdata.decode('ascii')
 print(data)


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

            # Add new socket to the list of sockets passed to select
            socket_list.append(conn)





    receive_message(sockt)
   

