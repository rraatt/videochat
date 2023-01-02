import base64
import os
import pickle
import queue
import struct
import threading
import time
from abc import ABC, abstractmethod

import cv2
import imutils
import numpy as np
import socket

BUFF_SIZE = 65536
PORT = 9699
PACKET_SIZE = 4096
WIDTH = 400


class VideoChat(ABC):

    def __init__(self):
        self.q = queue.Queue(maxsize=10)
        self.vid = cv2.VideoCapture(0)
        self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

    def __del__(self):
        self.connection_socket.close()

    def _generate_video(self):
        while self.vid.isOpened():
            try:
                _, frame = self.vid.read()
                frame = imutils.resize(frame, width=WIDTH)
                self.q.put(frame)
            except:
                os._exit(1)
            time.sleep(0.001)
        print('Player closed')
        self.vid.release()

    def start_chat(self):
        t1 = threading.Thread(target=self._get_message, args=())
        t2 = threading.Thread(target=self._send_message, args=())
        t1.start()
        t2.start()

    def start_video(self):
        t3 = threading.Thread(target=self._get_video, args=())
        t4 = threading.Thread(target=self._send_video, args=())
        t5 = threading.Thread(target=self._generate_video, args=())
        t3.start()
        t4.start()
        t5.start()

    @abstractmethod
    def _send_video(self):
        pass

    @abstractmethod
    def _get_message(self):
        pass

    @abstractmethod
    def _send_message(self):
        pass

    @abstractmethod
    def _get_video(self):
        pass


class Server(VideoChat):
    def __init__(self):
        super().__init__()
        host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(host_name)
        print(self.host_ip)
        socket_address = (self.host_ip, PORT)
        self.connection_socket.bind(socket_address)
        print('Listening at:', socket_address)

    def _send_video(self):
        cv2.namedWindow('SERVER TRANSMITTING VIDEO')
        cv2.moveWindow('SERVER TRANSMITTING VIDEO', 400, 30)
        msg, client_addr = self.connection_socket.recvfrom(BUFF_SIZE)
        print('GOT connection from ', client_addr)
        while True:
            frame = self.q.get()
            encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)
            self.connection_socket.sendto(message, client_addr)
            cv2.imshow('SERVER TRANSMITTING VIDEO', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                os._exit(1)
            time.sleep(0.01)

    def _send_message(self):
        s = socket.socket()
        s.bind((self.host_ip, (PORT - 1)))
        s.listen(5)
        client_socket, addr = s.accept()
        cnt = 0
        while True:
            if client_socket:
                while True:
                    print('SERVER TEXT ENTER BELOW:')
                    data = input()
                    a = pickle.dumps(data)
                    message = struct.pack("Q", len(a)) + a
                    client_socket.sendall(message)

                    cnt += 1
                    time.sleep(0.01)

    def _get_message(self):
        s = socket.socket()
        s.bind((self.host_ip, (PORT - 2)))
        s.listen(5)
        client_socket, addr = s.accept()
        data = b""
        payload_size = struct.calcsize("Q")

        while True:
            try:
                while len(data) < payload_size:
                    packet = client_socket.recv(4 * 1024)  # 4K
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                print('', end='\n')
                print('CLIENT TEXT RECEIVED:', frame, end='\n')
                print('SERVER TEXT ENTER BELOW:')
                time.sleep(0.001)

            except Exception:
                print('Your friend left conversation')
                client_socket.close()
                os._exit(1)

    def _get_video(self):
        cv2.namedWindow('SERVER RECEIVING VIDEO')
        cv2.moveWindow('SERVER RECEIVING VIDEO', 400, 360)
        video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        socket_address = (self.host_ip, PORT - 3)
        video_socket.bind(socket_address)
        while True:

            packet, _ = video_socket.recvfrom(BUFF_SIZE)
            data = base64.b64decode(packet, ' /')
            npdata = np.frombuffer(data, dtype=np.uint8)

            frame = cv2.imdecode(npdata, 1)
            cv2.imshow("SERVER RECEIVING VIDEO", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                video_socket.close()
                break

            time.sleep(0.001)
        cv2.destroyAllWindows()


class Client(VideoChat):
    """Class to initialize a client connection (connecting to person, who requested the call)
    manage messages and video signal"""

    def __init__(self, host_ip):
        super().__init__()
        self.host_ip = host_ip
        print(self.host_ip)
        message = b'Hello'
        self.connection_socket.sendto(message, (self.host_ip, PORT))

    def _get_message(self):
        """Creating a TCP socket and connecting to person, to receive messages"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_address = (self.host_ip, PORT - 1)
        print('server listening at', socket_address)
        client_socket.connect(socket_address)
        print("CLIENT CONNECTED TO", socket_address)
        data = b""
        payload_size = struct.calcsize("Q")
        while True:
            try:
                while len(data) < payload_size:
                    packet = client_socket.recv(PACKET_SIZE)
                    if not packet: break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                while len(data) < msg_size:
                    data += client_socket.recv(PACKET_SIZE)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                print('', end='\n')
                print('SERVER TEXT RECEIVED:', frame, end='\n')
                print('CLIENT TEXT ENTER BELOW:')
                time.sleep(0.01)
            except:
                break
        client_socket.close()
        print('closed')
        os._exit(1)

    def _get_video(self):
        cv2.namedWindow('Your friend webcam')
        cv2.moveWindow('Your friend webcam', 10, 360)
        while True:
            packet, _ = self.connection_socket.recvfrom(BUFF_SIZE)
            data = base64.b64decode(packet, ' /')
            npdata = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(npdata, 1)
            cv2.imshow("Your friend web cam", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.connection_socket.close()
                os._exit(1)
            time.sleep(0.001)

    def _send_message(self):
        """Creating a TCP socket for sending messages"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_address = (self.host_ip, PORT - 2)
        print('server listening at', socket_address)
        client_socket.connect(socket_address)
        print("msg send CLIENT CONNECTED TO", socket_address)
        while True:
            if client_socket:
                while True:
                    print('CLIENT TEXT ENTER BELOW:')
                    data = input()
                    a = pickle.dumps(data)
                    message = struct.pack("Q", len(a)) + a
                    client_socket.sendall(message)
                    time.sleep(0.01)

    def _send_video(self):
        socket_address = (self.host_ip, PORT - 3)
        print('server listening at', socket_address)
        cv2.namedWindow('Your webcam')
        cv2.moveWindow('Your webcam', 10, 30)
        while True:
            while True:
                frame = self.q.get()
                encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                message = base64.b64encode(buffer)
                self.connection_socket.sendto(message, socket_address)
                cv2.imshow('Your webcam', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    os._exit(1)
                time.sleep(0.001)


if __name__ == '__main__':
    obj = Server()  # 192.168.50.89
    obj.start_chat()

