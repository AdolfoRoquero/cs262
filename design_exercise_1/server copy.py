import socket
HOST = socket.gethostname()#'65.112.8.28'
print(HOST)
PORT = 6000



def server_ex():
 serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 serversocket.bind((HOST, PORT))
 serversocket.listen()
 clientsocket, addr = serversocket.accept()
 print('Connected to by:', addr)

 bdata = clientsocket.recv(128)
 data = bdata.decode('ascii')
 print(data)

server_ex()