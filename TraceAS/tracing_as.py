import re
import subprocess
from json import loads
from urllib import request
import argparse

ip_regex = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

phrases = {
    'ii': 'Не удается разрешить системное имя узла.\n',
    'tr': 'Трассировка маршрута',
    'hu': 'Заданный узел недоступен.\n',
    'tc': 'Трассировка завершена.\n',
    'mh': 'с максимальным числом прыжков'
}


class ASResponse:
    """
    Translate: отклик от автономной системы. Класс необходим
    для грамотной выдачи необходимой по заданию полей.
    """

    def __init__(self, json: dict):
        self._json = json
        self._parse()

    def _parse(self):
        """
        Парсер json-файла (вычленение нужной информации)
        """
        self.ip = self._json.get('ip') or '--'
        self.city = self._json.get('city') or '--'
        self.hostname = self._json.get('hostname') or '--'
        self.country = self._json.get('country') or '--'
        org = self._json.get('org')
        self.AS = '--' if org is None else org.split()[0]
        self.provider = '--' if org is None else ' '.join(org.split()[1:])


class Output:
    """
    Класс создан для отрисовки в консоли результатов трассировки.
    """
    _IP_LEN = 15
    _AS_LEN = 6
    _COUNTRY_CITY_LEN = 20

    def __init__(self):
        self._number = 1

    def print(self, ip: str, a_s: str, country: str, city: str, provider: str):
        """
        :param ip: IP-адрес
        :param a_s: Автономная система
        :param country: Страна
        :param city: Город
        :param provider: Провайдер
        :return: ничего - просто печатает строку.
        """
        if self._number == 1:
            self._print_header()
        string = f'{self._number}' + ' ' * (3 - len(str(self._number)))
        string += ip + self._spaces(self._IP_LEN, len(ip))
        string += a_s + self._spaces(self._AS_LEN, len(a_s))
        country_city = f'{country}/{city}'
        string += country_city + self._spaces(self._COUNTRY_CITY_LEN, len(country_city))
        string += provider
        self._number += 1
        print(string)

    @staticmethod
    def _print_header():
        """
        Вспомогательный метод: печатает заголовки таблицы.
        """
        print('№  IP' + ' ' * 16 + 'AS' + ' ' * 7 + 'Country/City' + ' ' * 11 + 'Provider')

    @staticmethod
    def _spaces(expected: int, actual: int) -> str:
        """
        Вспомогательный метод: допечатывает пробелы.
        :param expected: то количество символов, которое мы можем занять.
        :param actual: то количество символов, которое мы уже заняли.
        :return: строка пробелов в количестве, необходимом для красивой отрисовки таблицы.
        """
        return ' ' * (3 + (expected - actual))


def get_as_number_by_ip(ip) -> ASResponse:
    """
    По полученному ip-адресу вернуть объект отклика.
    :param ip:
    :return: ASResponse
    """
    return ASResponse(loads(request.urlopen('https://ipinfo.io/' + ip + '/json').read()))


def get_route(address: str):
    """
    Непосредственно функция получения пути следования пакета от нас до цели.
    """
    tracert = subprocess.Popen(['tracert', address], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    get_as = False
    output = Output()
    for line in iter(tracert.stdout.readline, ""):
        line = line.decode(encoding='cp866')
        if line.find(phrases['ii']) != -1:
            print(line)
            break
        elif line.find(phrases['tr']) != -1:
            print(line, end='')
            ending = ip_regex.findall(line)[0]
        elif line.find(phrases['mh']) != -1:
            get_as = True
        elif line.find(phrases['hu']) != -1:
            print(line.removeprefix(' '))
            break
        elif line.find(phrases['tc']) != -1:
            print(line)
            break

        try:
            ip = ip_regex.findall(line)[0]
        except IndexError:
            continue

        if get_as:
            response = get_as_number_by_ip(ip)
            output.print(response.ip, response.AS, response.country, response.city, response.provider)
            if ip == ending:
                print(phrases['tc'])
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('address', type=str)
    get_route(parser.parse_args().address)
