from socket import *

HOST = 'localhost'
PORT = 123
ADDR = (HOST, PORT)


class TimeClient:
    @staticmethod
    def start():
        udp_socket = socket(AF_INET, SOCK_DGRAM)
        udp_socket.sendto(b'tell me time', ADDR)
        data = udp_socket.recvfrom(1024)
        print(data[0].decode())
        udp_socket.close()


if __name__ == '__main__':
    TimeClient().start()
