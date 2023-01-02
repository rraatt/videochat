from client import *


class Server(VideoChat):
    def __init__(self):
        super().__init__()
        print(self.host_ip)
        print('Listening at:', (self.host_ip, PORT))

    def _get_message(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        while True:
            try:
                packet, _ = self.video_socket.recvfrom(BUFF_SIZE)
                data = base64.b64decode(packet, ' /')
                npdata = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(npdata, 1)
                cv2.imshow("SERVER RECEIVING VIDEO", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.video_socket.close()
                    break
                time.sleep(0.001)
            except socket.timeout:
                print("your friend left videochat")
                self.video_break.set()
                self.video_socket.close()
                break

    def _send_video(self):
        cv2.namedWindow('SERVER TRANSMITTING VIDEO')
        cv2.moveWindow('SERVER TRANSMITTING VIDEO', 400, 30)
        msg, client_addr = self.video_socket.recvfrom(BUFF_SIZE)
        print('GOT connection from ', client_addr)
        while True:
            frame = self.q.get()
            encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            message = base64.b64encode(buffer)
            self.video_socket.sendto(message, client_addr)
            cv2.imshow('SERVER TRANSMITTING VIDEO', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or self.video_break.is_set():
                cv2.destroyAllWindows()
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
