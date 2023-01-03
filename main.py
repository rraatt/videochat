import socket, pickle, struct
import pyshine as ps

mode = 'send'
name = 'CLIENT SENDING AUDIO'
audio, context = ps.audioCapture(mode=mode)
# ps.showPlot(context,name)

# create socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = '192.168.50.88'
port = 4982

socket_address = (host_ip, port)
client_socket.connect(socket_address)
print("CLIENT CONNECTED TO", socket_address)

if client_socket:
    while True:
        try:
            frame = audio.get()
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)

        except:
            print('AUDIO FINISHED!')
            break

client_socket.close()



