from socket import socket, AF_INET, SOCK_STREAM
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import base64
import sys
import ssl

MAIL_SERVERS = {'yandex.ru': ('smtp.yandex.ru', 465),
                'mail.ru': ('smtp.mail.ru', 465),
                'rambler.ru': ('smtp.rambler.ru ', 465),
                'gmail.com': ('smtp.gmail.com', 465)}


class Client:
    def __init__(self):
        self.sender, self.password, self.recipients, self.subject, self.attachments = self.check_config()
        self.mail_server = MAIL_SERVERS[self.sender.split('@')[1]]
        self.count_parcels = 0
        # переменная введена в попытке избежать отклонения отправки сообщения из-за подозрения на спам

    @staticmethod
    def check_config():
        """
        Проверяет cfg с целью нахождения необходимой информации.
        Выдает ошибку и останавливает работу, в случае несоответствия с вводом данных.
        :return: string, string, list[string], string, list[string]
        """
        try:
            with open('files/config.txt') as f:
                sender = f.readline()[:-1].split(' ')[1]
                password = f.readline()[:-1].split(' ')[1]
                recipients = f.readline()[:-1].split(' ')
                subject = f.readline()[:-1].partition(' ')[2]
                attachments = f.readline().split(' ')
                print(f'config.txt\n\n{sender = }\n{password = }\n{recipients = }\n{subject = }\n{attachments = }\n')
                return sender, password, recipients[1:], subject, attachments[1:]
        except Exception:
            print('Данные были введены не верно!\nПрочитайте README.md и введите данные корректно!')
            sys.exit()

    @staticmethod
    def request(s, r):
        """
        Выполнение запроса и получение ответа.
        :param s: socket
        :param r: type of request, e.g. EHLO, AUTH LOGIN etc.
        :return: decoded response from ...
        """
        s.send((r + '\n').encode())
        return s.recv(65535).decode()

    def start(self) -> None:
        """
        Этот класс был оставлен еще с пары и модифицирован под логику моего класса без потери функциональности.
        Может отправлять сообщения в соответствии с поставленной задачей, но без вложений.
        """
        for recipient in self.recipients:
            with socket(AF_INET, SOCK_STREAM) as client:
                client.connect(self.mail_server)
                client = ssl.wrap_socket(client)
                print(self.request(client, f'EHLO {self.sender.split("@")[0]}'))
                base64_auth = base64.b64encode(('\x00' + self.sender + '\x00' + self.password).encode()).decode()
                print(self.request(client, 'AUTH PLAIN'))
                print(self.request(client, base64_auth))
                print(self.request(client, f'MAIL FROM: {self.sender}'))
                print(self.request(client, f'RCPT TO: {recipient}'))
                print(self.request(client, 'DATA'))
                print(self.request(client, self.get_message(recipient)))
                print(self.request(client, 'QUIT'))

    def get_message(self, recipient) -> str:
        """
        Непосредственно создание сообщения с необходимыми полями
        :param recipient:
        :return: message, string
        """
        with open('files/message.txt', 'r', encoding='utf-8') as f:
            message = f.read()
        self.count_parcels += 1
        return f"From: {self.sender}\nTo: {recipient}\nSubject: {self.subject}\nContent-Type: text/plain\n\n{message + ' ' * self.count_parcels}\n.\n"

    def start_with_smtplib(self) -> None:
        """
        Запуск клиента и отправка сообщения с вложениями (?) кому-либо.
        """
        try:
            client = smtplib.SMTP_SSL(*self.mail_server)
            client.login(self.sender, self.password)
            message = self.get_message_with_smtplib()
            # print(message)
            client.sendmail(self.sender, self.recipients, message)
            client.quit()
            print('Email delivered successfully!')
        except smtplib.SMTPRecipientsRefused:
            print('Email delivery failed, invalid recipient')
        except smtplib.SMTPAuthenticationError:
            print('Email delivery failed, authorization error')
        except smtplib.SMTPSenderRefused:
            print('Email delivery failed, invalid sender')
        except smtplib.SMTPConnectError:
            print('Email delivery failed, failure in connect')
        except smtplib.SMTPException as e:
            print('Email delivery failed, ', e)

    def get_message_with_smtplib(self) -> str:
        """
        Создание сообщения с необходимыми полями и вложениями.
        :return: message, string
        """
        message = MIMEMultipart("mixed") if self.attachments else MIMEMultipart("alternative")
        message['Subject'] = self.subject
        message['From'] = self.sender
        message['To'] = ','.join(self.recipients)
        alternative = MIMEMultipart('alternative')
        with open("files/message.txt", 'r', encoding='utf-8') as f:
            alternative.attach(MIMEText(f.read()))
        message.attach(alternative)
        self.load_attachments(message)
        return message.as_string()

    def load_attachments(self, message):
        """
        Метод был создан просто так, понятно, что он добавляет
        вложения в сообщение, если таковые конечно есть.
        :param message: MIMEMultipart,
        :return: message: MIMEMultipart with attachments, if they exist.
        """
        for attachment in self.attachments:
            a = MIMEApplication(open(f'files/attachments/{attachment}', 'rb').read())
            a.add_header('Content-Disposition', 'attachment', filename=attachment)
            message.attach(a)


if __name__ == '__main__':
    Client().start_with_smtplib()
