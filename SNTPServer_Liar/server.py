from socket import *
import datetime

HOST = 'localhost'
PORT = 123
ADDR = (HOST, PORT)
CFG = 'config.txt'


class TimeServer:
    def __init__(self, config):
        self.time_offset, self.sign = self.get_offset(config)

    @staticmethod
    def get_offset(file: str) -> (int, int):
        try:
            with open(file) as f:
                offset = f.readline()
                if offset.isdigit():
                    return int(offset), 1
                elif offset[0] == '-' and offset[1:].isdigit():
                    return int(offset), -1
                else:
                    return 0, 0
        except Exception:
            return 0, 0

    def start(self):
        with socket(AF_INET, SOCK_DGRAM) as udp_socket:
            udp_socket.bind(ADDR)
            while 1:
                conn, addr = udp_socket.recvfrom(1024)
                print('client addr: ', addr)
                if conn.decode() == 'tell me time':
                    message = f'current time is {self.get_wrong_time()}'
                    # print(message)
                    udp_socket.sendto(message.encode(), addr)

    def get_wrong_time(self) -> str:
        return (datetime.datetime.now() + self.sign * datetime.timedelta(seconds=self.time_offset)).strftime('%H:%M:%S')


if __name__ == '__main__':
    TimeServer(CFG).start()
