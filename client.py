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
import pyaudio

BUFF_SIZE = 65536
VIDEO_PORT = 9699
AUDIO_PORT = 9696
MESSAGE_PORT = 9698
PACKET_SIZE = 4096
WIDTH = 400
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


class VideoChat(ABC):
    """Father class with required setup for initiating text chat + video chat connection, abstract methods required for
    implementation in ClientActive and ClientPassive classes"""

    def __init__(self):
        """Initiating sockets, event to stop threads in case of disconnection"""
        self.client_socket = None
        self.q = queue.Queue(maxsize=10)  # Queue for webcam frames
        self.vid = cv2.VideoCapture(0)  # Webcam feed
        host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(host_name)
        self.video_break = threading.Event()
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Socket used for video connection
        self.video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        socket_address = (self.host_ip, VIDEO_PORT)
        self.video_socket.bind(socket_address)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Socket used for audio connection
        self.audio_socket.bind((self.host_ip, AUDIO_PORT))

    def __del__(self):
        self.video_socket.close()
        self.audio_socket.close()
        self.client_socket.close()

    def _generate_video(self):
        """Generating video feed from webcam"""
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

    @abstractmethod
    def start_chat(self):
        self.client_socket.settimeout(None)
        t1 = threading.Thread(target=self._send_message, args=())
        t2 = threading.Thread(target=self._get_message, args=())
        t1.start()
        t2.start()

    def start_video(self):
        t1 = threading.Thread(target=self._send_video, args=())
        t2 = threading.Thread(target=self._generate_video, args=())
        t3 = threading.Thread(target=self._get_video, args=())
        t1.start()
        t2.start()
        t3.start()

    def start_audio(self, friend_ip):
        p = pyaudio.PyAudio()
        audio_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                              output=True, frames_per_buffer=CHUNK)  # Creating audio stream for voice
        t1 = threading.Thread(target=self._send_audio, args=(friend_ip, audio_stream, p))
        t2 = threading.Thread(target=self._get_audio, args=(audio_stream,))
        t1.start()
        t2.start()

    def _send_audio(self, friend_ip, audio_stream, p):
        while True:
            data = audio_stream.read(CHUNK)
            self.audio_socket.sendto(data, (friend_ip, AUDIO_PORT))
            if self.video_break.is_set():
                break
        audio_stream.stop_stream()
        audio_stream.close()
        p.terminate()

    def _get_audio(self, audio_stream):
        while True:
            data, addr = self.audio_socket.recvfrom(CHUNK * CHANNELS * 2)
            audio_stream.write(data)
            if self.video_break.is_set():
                break

    @abstractmethod
    def _send_video(self):
        self.video_break.clear()

    def _get_message(self):
        """Getting messages from a TCP socket"""
        data = b""
        payload_size = struct.calcsize("Q")
        while True:
            try:
                while len(data) < payload_size:
                    packet = self.client_socket.recv(PACKET_SIZE)
                    if not packet:
                        break
                    data += packet
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]  # Getting the size of message from message header
                while len(data) < msg_size:
                    data += self.client_socket.recv(PACKET_SIZE)
                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)  # received message
                print('', end='\n')
                print('TEXT RECEIVED:', frame, end='\n')
                print('TEXT ENTER BELOW:')
                time.sleep(0.001)
            except Exception:
                print('Your friend left conversation')
                self.client_socket.close()
                os._exit(1)

    def _send_message(self):
        """Sending messages over TCP socket"""
        while True:
            if self.client_socket:
                while True:
                    print('SERVER TEXT ENTER BELOW:')
                    data = input()
                    a = pickle.dumps(data)
                    message = struct.pack("Q", len(a)) + a
                    self.client_socket.sendall(message)
                    time.sleep(0.01)

    @abstractmethod
    def _get_video(self):
        pass


class ClientPassive(VideoChat):
    """Class for creating sockets of side waiting for connection and managing video transmission"""
    def __init__(self):
        super().__init__()
        self.client_address = None  # Field for storing clients address
        print(self.host_ip)

    def start_chat(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host_ip, MESSAGE_PORT))
            s.settimeout(60)
            s.listen(5)
            self.client_socket, self.client_address = s.accept()
        super().start_chat()

    def _get_video(self):
        """Getting video feed from socket, in case of connection timeout or user initiated disconnect set video_break event
        to stop video and audio transmission"""
        self.video_socket.settimeout(10)  # Timeout in case of second user disconnection
        while True:
            try:
                packet, _ = self.video_socket.recvfrom(BUFF_SIZE)
                data = base64.b64decode(packet, ' /')
                npdata = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(npdata, 1)
                cv2.imshow("SERVER RECEIVING VIDEO", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.video_socket.settimeout(None)
                    self.video_break.set()
                    SystemExit()
                time.sleep(0.001)
            except socket.timeout:
                print("your friend left videochat")
                self.video_break.set()
                self.video_socket.settimeout(None)
                SystemExit()

    def _send_video(self):
        """Initiation a handshake process with second user and starting video and audio transmission"""
        self.start_audio(self.client_address[0])  # starting audio transmission to active user
        while True:
            frame = self.q.get()
            encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)
            self.video_socket.sendto(message, (self.client_address[0], VIDEO_PORT))
            cv2.imshow('SERVER TRANSMITTING VIDEO', frame)
            cv2.waitKey(1) & 0xFF
            if self.video_break.is_set():  # in case of disconnection destroy video windows
                cv2.destroyAllWindows()
                SystemExit()
            time.sleep(0.01)


class ClientActive(VideoChat):
    """Class to initialize a client connection (connecting to person, who requested the call)
    manage messages and video signal"""

    def __init__(self, server_ip):
        super().__init__()
        self.server_ip = server_ip
        print(self.server_ip)

    def start_chat(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_address = (self.server_ip, MESSAGE_PORT)
        self.client_socket.settimeout(60)
        self.client_socket.connect(socket_address)
        super().start_chat()

    def _get_video(self):
        self.video_socket.settimeout(10)
        while True:
            try:
                packet, _ = self.video_socket.recvfrom(BUFF_SIZE)
                data = base64.b64decode(packet, ' /')
                npdata = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(npdata, 1)
                cv2.imshow("Your friend web cam", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.video_socket.settimeout(None)
                    self.video_break.set()
                    SystemExit()
                time.sleep(0.001)
            except socket.timeout:
                print("your friend left videochat")
                self.video_break.set()
                self.video_socket.settimeout(None)
                SystemExit()

    def _send_video(self):
        self.start_audio(self.server_ip)
        while True:
            while True:
                frame = self.q.get()
                encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                message = base64.b64encode(buffer)
                self.video_socket.sendto(message, (self.server_ip, VIDEO_PORT))
                cv2.imshow('Your webcam', frame)
                cv2.waitKey(1) & 0xFF
                if self.video_break.is_set():
                    cv2.destroyAllWindows()
                    SystemExit()
                time.sleep(0.001)


if __name__ == '__main__':
    #obj = Client('192.168.50.156')  # '192.168.50.89'
    obj = ClientPassive()
    obj.start_chat()
