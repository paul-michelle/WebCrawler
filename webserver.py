import json
import settings
import format_utils
import email.message
import re
import socket
import sys
from typing import List
from email.parser import Parser as mail_parser
from urllib.parse import urlparse
from saver import TextFileSaver
from collector import ValidDataCollector

MAX_LINE_BINARY_LENGTH = 64 * 1024
MAX_HEADERS_LINES = 50
CONTENT_TYPE = 'application/json; charset=utf-8'
UUID_LENGTH = 32

_some_collector = []  # to be changed fo self.__collector


class HTTPServer:

    def __init__(self, host, port, server_name,
                 saver=TextFileSaver(settings.TARGET_DIR_PATH),
                 collector=ValidDataCollector(settings.POSTS_FOR_PARSING_NUM)):
        self._host = host
        self._port = port
        self._server_name = server_name
        self.__saver = saver
        self.__collector = collector

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
                    print('Client serving failed:', e)

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
        raise Exception('Bad request. Improper or missing "Host" header')

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
        if request.path == '/posts/' and request.method == 'POST':
            return self.write_next_post()

        if not self.__saver.filename_calculated:
            return HTTPResponse(status=404, reason='File to save parsed data was never created')

        if request.path == '/posts/' and request.method == 'GET':
            return self.get_all_written_posts()

        single_post_crud = re.search('/posts/[\w]*/', request.path)
        unique_id = request.path.split('/')[2]
        if len(unique_id) != UUID_LENGTH:
            return HTTPResponse(status=404, reason='Inadequate unique_id length. 32 chars expected')

        if single_post_crud and request.method == 'GET':
            return self.retrieve_post(unique_id)

        if single_post_crud and request.method == 'PUT':
            return self.update_post(request)

        if single_post_crud and request.method == 'DELETE':
            return self.delete_post(unique_id)

        return HTTPResponse(status=404, reason='Not found')

    def get_all_written_posts(self):
        with open(self.__saver.absolute_path, 'r') as f:
            already_written_lines = f.readlines()
        response_text = [format_utils.inline_values_to_dict(line) for line in already_written_lines]
        response_body = json.dumps(response_text).encode('utf-8')
        headers = [('Content-Type', CONTENT_TYPE), ('Content-Length', len(response_body))]
        return HTTPResponse(status=200, reason='OK', headers=headers, body=response_body)

    def write_next_post(self):
        # if self.__collector.is_empty:
        if len(_some_collector) == 0:
            return HTTPResponse(status=404, reason='All parsed data exhausted')
        if not self.__saver.filename_calculated:
            self.__saver.calculate_filename()
        with open(self.__saver.absolute_path, 'a') as f:
            # post_to_append = self.__collector.pop(0)
            post_to_append = _some_collector.pop(0)
            f.write(post_to_append + '\n')

        unique_id = post_to_append.split(';')[0]
        response_body = json.dumps({'unique_id': f'{unique_id}'}).encode('utf-8')
        headers = [('Content-Type', CONTENT_TYPE), ('Content-Length', len(response_body))]
        return HTTPResponse(status=201, reason='Created', headers=headers, body=response_body)

    def retrieve_post(self, unique_id: str) -> object:
        with open(self.__saver.absolute_path, 'r') as f:
            already_written_lines = f.readlines()
        for line in already_written_lines:
            if line.startswith(unique_id):
                response_text = format_utils.inline_values_to_dict(line)
                response_body = json.dumps(response_text).encode('utf-8')
                headers = [('Content-Type', CONTENT_TYPE), ('Content-Length', len(response_body))]
                return HTTPResponse(status=200, reason='OK', headers=headers, body=response_body)
        return HTTPResponse(status=404, reason='Entry not found in txt file')

    def update_post(self, request):
        update_made = False
        sent_info = json.loads(request.body.decode('utf-8'))
        if not format_utils.info_is_valid(sent_info):
            return HTTPResponse(status=404, reason='Improper request body')
        with open(self.__saver.absolute_path, 'r+') as f:
            already_written_lines = f.readlines()
            f.seek(0)
            for line in already_written_lines:
                if line.startswith(sent_info['unique_id']):
                    line = format_utils.dict_to_values_inline(sent_info)
                    update_made = True
                f.write(line)
        if update_made:
            return HTTPResponse(status=200, reason='Entry successfully updated')
        return HTTPResponse(status=404, reason='Entry not found in txt file')

    def delete_post(self, unique_id: str) -> object:
        with open(self.__saver.absolute_path, 'r+') as f:
            already_written_lines = f.readlines()
            f.seek(0)
            for line in already_written_lines:
                if not line.startswith(unique_id):
                    f.write(line)
            f.truncate()
            f.seek(0)
            if len(f.readlines()) == len(already_written_lines):
                return HTTPResponse(status=404, reason='Entry not found in txt file')
        return HTTPResponse(status=204, reason='Post deleted')

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

    @property
    def body(self):
        body_size = self.headers.get('Content-Length')
        if body_size:
            return self.file_to_read.read(int(body_size))


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
