import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from struct import pack

MAX_PORT = 65535
PACKET = b'\x13' + b'\x00' * 39 + b'\x6f\x89\xe9\x1a\xb6\xd5\x3b\xd3'


class Arguments:
    """
    Класс создан для облегчения работы с аргументами, поступающими на вход.
    """

    def __init__(self):
        self.host, self.start, self.end = self._parse_args()

    @staticmethod
    def _parse_args() -> tuple[str, int, int]:
        """
        Непосредственно парсер аргументов.
        :return: Tuple(host, start, end)
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', type=str, dest='host', default='localhost', help='host to scan')
        parser.add_argument('ports', type=str, help='port or range of ports: 1 or 1..100')
        arguments = parser.parse_args()
        try:
            if '..' in arguments.ports:
                start, end = [int(elem) for elem in arguments.ports.split('..')]
            else:
                start, end = int(arguments.ports), int(arguments.ports)
        except ValueError:
            print('Ports must be integer')
            sys.exit()
        if end > MAX_PORT:
            print('Ports must be less than 65535')
            sys.exit()
        if start > end:
            print('Invalid ports')
            sys.exit()
        try:
            socket.gethostbyname(arguments.host)
        except socket.gaierror:
            print(f'Invalid host {arguments.host}')
            sys.exit()
        return arguments.host, start, end


"""
Последующие 5 классов отвечают за соответствующие протоколы, 
а точнее за проверку принадлежности к таковым. 
"""


class DNS:
    @staticmethod
    def is_dns(packet: bytes) -> bool:
        transaction_id = PACKET[:2]
        return transaction_id in packet


class SNTP:
    @staticmethod
    def is_sntp(packet: bytes) -> bool:
        transmit_timestamp = PACKET[-8:]
        origin_timestamp = packet[24:32]
        is_packet_from_server = 7 & packet[0] == 4
        return len(packet) >= 48 and is_packet_from_server and origin_timestamp == transmit_timestamp


class POP3:
    @staticmethod
    def is_pop3(packet: bytes) -> bool:
        return packet.startswith(b'+')


class HTTP:
    @staticmethod
    def is_http(packet: bytes) -> bool:
        return b'HTTP' in packet


class SMTP:
    @staticmethod
    def is_smtp(packet: bytes) -> bool:
        return packet[:3].isdigit()


class Scanner:
    """
    Класс Scanner создан для выполнения поставленной задачи.
    """
    _PROTOCOL_DEFINER = {
        'SMTP': lambda packet: SMTP.is_smtp(packet),
        'DNS': lambda packet: DNS.is_dns(packet),
        'POP3': lambda packet: POP3.is_pop3(packet),
        'HTTP': lambda packet: HTTP.is_http(packet),
        'SNTP': lambda packet: SNTP.is_sntp(packet)
    }

    def __init__(self, host: str):
        self._host = host

    def tcp_port(self, port: int) -> str:
        """
        Проверка доступности (открытости) TCP порта.
        :param port: port (int())
        :return: if port is open, returns the message of open port
        (and maybe protocol name which is working on port),
        else empty string
        """
        socket.setdefaulttimeout(0.5)
        result = ''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self._host, port))
                result = f'TCP port - {port} - is open.'
            except (socket.timeout, TimeoutError, OSError):
                pass
            try:
                sock.send(pack('!H', len(PACKET)) + PACKET)
                data = sock.recv(1024)
                result += f' {self._check(data)}'
            except socket.error:
                pass
        return result

    def udp_port(self, port: int) -> str:
        """
        Проверка доступности (открытости) UDP порта.
        :param port: port (int())
        :return: if port is open, returns the message of open port
        (and maybe protocol name which is working on port),
        else empty string
        """
        socket.setdefaulttimeout(3)
        result = ''
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                sock.sendto(PACKET, (self._host, port))
                data, _ = sock.recvfrom(1024)
                result = f'UDP port - {port} - is open. {self._check(data)}'
            except socket.error:
                pass
        return result

    def _check(self, data: bytes) -> str:
        """
        Проверка соответствие одному из данных протоколов
        :param data: stream of data bytes
        :return: name of protocol (str()) if it's found else empty string ('')
        """
        for protocol, checker in self._PROTOCOL_DEFINER.items():
            if checker(data):
                return protocol
        return ''


def main(host: str, start: int, end: int):
    with ThreadPoolExecutor(max_workers=500) as pool:
        for port in range(start, end + 1):
            pool.submit(execute, Scanner(host), port)


def execute(scanner: Scanner, port: int):
    show(scanner.tcp_port(port))
    show(scanner.udp_port(port))


def show(result: str):
    if result:
        print(result)


if __name__ == "__main__":
    a = Arguments()
    main(a.host, a.start, a.end)
