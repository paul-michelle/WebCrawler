import json
import settings
import email.message
import os
import re
import socket
import sys
from typing import List
from email.parser import Parser as mail_parser
from urllib.parse import urlparse

MAX_LINE_BINARY_LENGTH = 64 * 1024
MAX_HEADERS_LINES = 50
CONTENT_TYPE = 'application/json; charset=utf-8'


class HTTPServer:

    def __init__(self, host, port, server_name, target_dir_path=settings.TARGET_DIR_PATH):
        self._host = host
        self._port = port
        self._server_name = server_name
        self.__target_dir_path = target_dir_path

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
        print(headers)
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
            decoded_next_raw_bytes_line = str(next_raw_bytes_line, 'iso-8859-1')
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
        new_file_created = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(self.__target_dir_path)))
        if new_file_created:
            with open(f'{self.__target_dir_path}{os.sep}{new_file_created.group()}', 'r') as new_file:
                file_contents = new_file.readlines()
            response_body = json.dumps(file_contents).encode('utf-8')
            headers = [('Content-Type', CONTENT_TYPE), ('Content-Length', len(response_body))]
            return HTTPResponse(status=200, reason='OK', headers=headers, body=response_body)

    def write_next_post(self, request):
        new_file_created = re.search('reddit-[0-9]{12}.txt', ''.join(os.listdir(self.__target_dir_path)))
        if not new_file_created:
            pass

    def retrieve_post(self, request):
        pass

    def update_post(self, request):
        pass

    def delete_post(self, request):
        pass

    @staticmethod
    def send_response(connection_established, response):
        file_to_write = connection_established.makefile('wb')
        status_line = f'HTTP/1.1 {response.status} {response.reason}\r\n'.encode('iso-8859-1')
        file_to_write.write(status_line)

        if response.headers:
            for (key, value) in response.headers:
                header_line = f'{key}: {value}\r\n'.encode('iso-8859-1')
                file_to_write.write(header_line)

        file_to_write.write(b'\r\n')

        if response.body:
            file_to_write.write(response.body)

        file_to_write.flush()
        file_to_write.close()

    # def send_error(self, connection_established, error):
    #     try:
    #         status = error.status
    #         reason = error.reason
    #     except:
    #         status = 500
    #         reason = b'Error on server side'
    #     response = HTTPResponse(status=status, reason=reason)
    #     self.send_response(connection_established, response)


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


class HTTPResponse:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    server_name = sys.argv[3]
    server = HTTPServer(host, port, server_name)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Connection has been voluntarily interrupted')
