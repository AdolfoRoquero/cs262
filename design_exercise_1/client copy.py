import socket
HOST = "10.250.227.245"
PORT = 6000
def client_soc ():
    # socket.gethostname() this returns the local network IP
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((HOST, PORT))

    msg = "CS 143!!!!"
    bmsg = msg.encode("ascii")
    sent = clientsocket.send(bmsg)
    print('Message sent, %d/%d bytes transmitted' % (sent, len(msg)))
    print(socket.gethostname())
    clientsocket.close()

client_soc()