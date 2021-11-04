import email.message
import re
import socket
import sys
from typing import List
from email.parser import Parser as mail_parser
from urllib.parse import urlparse

MAX_LINE_BINARY_LENGTH = 64 * 1024
MAX_HEADERS_LINES = 10


class HTTPServer:

    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name

    def serve_forever(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        try:
            server_socket.bind((self._host, self._port))
            server_socket.listen()

            while True:
                connection, _ = server_socket.accept()
                try:
                    self.serve_client(connection)
                except Exception as e:
                    print('Client serving failed', e)

        finally:
            server_socket.close()

    def serve_client(self, connection_established):
        request = self.form_http_request(connection_established)
        response = self.handle_http_request(request)
        self.send_response(connection_established, response)
        if connection_established:
            connection_established.close()

    def form_http_request(self, connection_established):
        file_to_read = connection_established.makefile('rb')
        method, target, http_version = self.parse_request_line(file_to_read)
        headers = self.parse_headers(file_to_read)
        host_specified = headers.get('Host')
        if host_specified in (self._server_name, f'{self._server_name}:{self._port}'):
            return HTTPRequest(method, target, http_version, headers, file_to_read)
        raise Exception('Bad request. Improper or missing "Host":.. header')

    @staticmethod
    def parse_request_line(file_to_read) -> List:
        first_raw_bytes_line = file_to_read.readline(MAX_LINE_BINARY_LENGTH + 1)
        if len(first_raw_bytes_line) > MAX_LINE_BINARY_LENGTH:
            raise Exception('The request line length exceeded')
        decoded_line = str(first_raw_bytes_line, 'iso-8859-1').strip()
        words_in_request_line = decoded_line.split()
        if len(words_in_request_line) != len(['method', 'target', 'version']):
            raise Exception('Improper request line. Request line should describe method, target, and HTTP-version')
        return words_in_request_line

    @staticmethod
    def parse_headers(file_to_read) -> email.message.Message:
        headers: List = []
        while True:
            next_raw_bytes_line = file_to_read.readline(MAX_LINE_BINARY_LENGTH + 1)
            if len(next_raw_bytes_line) > MAX_LINE_BINARY_LENGTH:
                raise Exception('The headers line length exceeded')
            if next_raw_bytes_line in (b'\r\n', b'\n', b''):
                break
            decoded_next_raw_bytes_line = str(next_raw_bytes_line, 'iso-8859-1').strip()
            headers.append(decoded_next_raw_bytes_line)
            if len(headers) > MAX_HEADERS_LINES:
                raise Exception(f'Max headers lines number exceeded. Limit is {MAX_HEADERS_LINES}')
        return mail_parser().parsestr(''.join(headers))

    def handle_http_request(self, request):
        if request.path == '/posts/' and request.method == 'GET':
            return self.get_all_written_posts(request)

        if request.path == '/posts/' and request.method == 'POST':
            return self.write_next_post(request)

        single_post_crud = re.search('/posts/[\w]{32}]', request.path)

        if single_post_crud and request.method == 'GET':
            return self.retrieve_post(request)

        if single_post_crud and request.method == 'PUT':
            return self.update_post(request)

        if single_post_crud and request.method == 'DELETE':
            return self.delete_post(request)

    def get_all_written_posts(self, request):
        pass

    def write_next_post(self, request):
        pass

    def retrieve_post(self, request):
        pass

    def update_post(self, request):
        pass

    def delete_post(self, request):
        pass

    def send_response(self, connection, response):
        pass

    def send_error(self, connection, error):
        pass


class HTTPRequest:
    def __init__(self, method, target, http_version, headers, file_to_read):
        self.method = method
        self.target = target
        self.version = http_version
        self.headers = headers
        self.file_to_read = file_to_read

    @property
    def path(self):
        url = urlparse(self.target)
        return url.path


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    server_name = sys.argv[3]
    server = HTTPServer(host, port, server_name)
    server.serve_forever()
