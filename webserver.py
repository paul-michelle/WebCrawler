"""Run a server on localhost.

The module allows working with the output file via simple RESTful API.
The request sent to localhost are parsed by the webserver corresponding method.
The crud-commands in the request are performed with an executor (txt, sql, nosql)
with the responses formed and sent back to the client."""

import io
import time
import collections
import heapq
import select
import utils
import logging
import email.message
import re
import socket
import json
from datetime import datetime
from uuid import UUID
from typing import List, Any, Coroutine, Union, Callable, Optional
from email.parser import Parser as mail_parser
from urllib.parse import urlparse
from crud_executors import base_crud_executor
from collector import ValidDataCollector

MAX_BYTES = 10_000
MAX_LINE_BINARY_LENGTH = 64 * 1024
MAX_HEADERS_LINES = 50


class HTTPRequest:
    def __init__(self, method: str, target: str, http_version: str,
                 headers: email.message.Message, file_to_read: io.BytesIO):
        self._method = method
        self._target = target
        self._version = http_version
        self._headers = headers
        self._file_to_read = file_to_read

    @property
    def method(self):
        return self._method

    @property
    def path(self):
        url = urlparse(self._target)
        return url.path

    @property
    def body(self):
        body_size = self._headers.get('Content-Length')
        if body_size:
            return self._file_to_read.read(int(body_size))


class HTTPResponse:
    def __init__(self, status: int, reason: str,
                 headers: List = None, body: bytes = None):
        self._status = status
        self._reason = reason
        self._headers = headers
        self._body = body

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    @property
    def headers_sent(self):
        return self._headers

    @property
    def body_sent(self):
        return self._body


class HTTPServer:

    def __init__(self, host: str, port: int, server_name: str,
                 executor: base_crud_executor.BaseCrudExecutor,
                 collector: ValidDataCollector):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._executor = executor
        self._collector = collector
        self._server_socket = None
        self._set_server_socket()

    def _set_server_socket(self) -> None:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.listen(1)

    def run_forever(self):
        scheduler.add_task(self._accept_client())
        scheduler.run()

    async def _accept_client(self) -> None:
        while True:
            client_socket, _ = await scheduler.accept(self._server_socket)
            scheduler.add_task(self._serve_client(client_socket))

    async def _serve_client(self, client_socket: socket.socket) -> None:
        while True:
            data = await scheduler.recv(client_socket)
            if not data:
                break
            http_request = self.form_http_request(io.BytesIO(data))
            http_response = await self.handle_http_request(http_request)
            data_to_send = self.get_data_to_send(http_response)
            await scheduler.send(client_socket, data_to_send)

        client_socket.close()

    def form_http_request(self, data: io.BytesIO) -> Optional[HTTPRequest]:
        method, target, http_version = self.parse_request_line(data)
        headers = self.parse_headers_block(data)
        host_specified = headers.get('Host')
        if host_specified in (self._server_name, f'{self._server_name}:{self._port}'):
            return HTTPRequest(method, target, http_version, headers, data)
        logging.error('Bad request. Improper or missing "Host" header')

    @staticmethod
    def parse_request_line(file_to_read: io.BytesIO) -> List[str]:
        first_raw_bytes_line = file_to_read.readline(MAX_LINE_BINARY_LENGTH + 1)
        if len(first_raw_bytes_line) > MAX_LINE_BINARY_LENGTH:
            raise Exception('The request line length exceeded')
        decoded_line = str(first_raw_bytes_line, 'iso-8859-1').strip()
        words_in_request_line = decoded_line.split()
        if len(words_in_request_line) != len(['method', 'target', 'version']):
            raise Exception('Improper request line. Request line should describe method, target, and HTTP-version')
        return words_in_request_line

    @staticmethod
    def parse_headers_block(file_to_read: io.BytesIO) -> email.message.Message:
        headers = []
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

    async def handle_http_request(self, request: HTTPRequest) -> Union[Callable, HTTPResponse]:
        if not request:
            return HTTPResponse(status=400, reason='Bad Request')

        if self._collector.is_empty and request.method == 'POST':
            return HTTPResponse(status=404, reason='All parsed data exhausted')

        if request.path == '/posts/remaining/' and request.method == 'POST':
            return self.write_remaining_posts()

        if request.path == '/posts/' and request.method == 'POST':
            await scheduler.sleep(10)
            return self.write_next_post()

        if self._collector.is_full:
            return HTTPResponse(status=404, reason='No written entries yet')

        if request.path == '/posts/' and request.method == 'GET':
            return self.retrieve_all_written_posts()

        single_post_crud = re.search('/posts/[\w-]+/', request.path)
        unique_id = request.path.split('/')[2]
        try:
            UUID(unique_id)
        except ValueError:
            return HTTPResponse(status=404, reason='Inadequate unique_id in uri')

        if single_post_crud and request.method == 'GET':
            return self.retrieve_post(unique_id)

        if single_post_crud and request.method == 'PUT':
            return self.update_post(request, unique_id)

        if single_post_crud and request.method == 'DELETE':
            return self.delete_post(unique_id)

        return HTTPResponse(status=404, reason='Not found')

    def write_remaining_posts(self) -> HTTPResponse:
        posts_to_append = self._collector.data
        unique_ids = self._executor.insert(posts_to_append)
        response_body = b', '.join(json.dumps({'unique_id': f'{unique_id}'}).encode('utf-8')
                                   for unique_id in unique_ids)
        headers = utils.form_headers(response_body)
        self._collector.clear()
        logging.info(f'All remaining data taken out of collector and saved --- {datetime.now()}')
        return HTTPResponse(status=201, reason='Created', headers=headers, body=response_body)

    def write_next_post(self) -> HTTPResponse:
        post_to_append = self._collector.get_one_entry()
        unique_id = self._executor.insert(post_to_append)
        response_body = json.dumps({'unique_id': f'{unique_id}'}).encode('utf-8')
        headers = utils.form_headers(response_body)
        return HTTPResponse(status=201, reason='Created', headers=headers, body=response_body)

    def retrieve_all_written_posts(self) -> HTTPResponse:
        posts_found = self._executor.find()
        if posts_found:
            response_body = json.dumps(posts_found).encode('utf-8')
            headers = utils.form_headers(response_body)
            return HTTPResponse(status=200, reason='OK', headers=headers, body=response_body)

    def retrieve_post(self, unique_id: str) -> HTTPResponse:
        post_found = self._executor.find(unique_id)
        if post_found:
            response_body = json.dumps(post_found).encode('utf-8')
            headers = utils.form_headers(response_body)
            return HTTPResponse(status=200, reason='OK', headers=headers, body=response_body)
        return HTTPResponse(status=404, reason='Entry not found')

    def update_post(self, request: HTTPRequest, unique_id: str) -> HTTPResponse:
        try:
            sent_info = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HTTPResponse(status=400, reason='Bad Request')

        if not utils.info_is_valid(sent_info, unique_id):
            return HTTPResponse(status=404, reason='Improper request body')

        update_performed = self._executor.update(sent_info, unique_id)
        if update_performed:
            return HTTPResponse(status=200, reason='Entry successfully updated')
        return HTTPResponse(status=404, reason='Update failure')

    def delete_post(self, unique_id: str) -> HTTPResponse:
        deletion_performed = self._executor.delete(unique_id)
        if deletion_performed:
            return HTTPResponse(status=204, reason='Entry deleted')
        return HTTPResponse(status=404, reason='Entry not found')

    @staticmethod
    def get_data_to_send(response: HTTPResponse) -> bytes:
        data_to_send = b''
        status_line = f'HTTP/1.1 {response.status} {response.reason}\r\n'.encode('iso-8859-1')
        data_to_send += status_line
        if response.headers_sent:
            for (key, value) in response.headers_sent:
                header_line = f'{key}: {value}\r\n'.encode('iso-8859-1')
                data_to_send += header_line
        data_to_send += b'\r\n'
        if response.body_sent:
            data_to_send += response.body_sent
        return data_to_send


class QueueClosed(Exception):
    pass


class Awaitable:
    def __await__(self):
        yield


class Scheduler:

    def __init__(self):
        self._tasks_ready = collections.deque()
        self._tasks_delayed = []
        self._sequence = 0
        self._current = None
        self._read_waiting = {}
        self._write_waiting = {}

    def set_current(self, task: Optional['Task']) -> None:
        self._current = task

    def get_current(self) -> Optional['Task']:
        return self._current

    def add_to_tasks_ready(self, task: 'Task') -> None:
        self._tasks_ready.append(task)

    def call_soon(self, func: Callable[[...], Any], delayed: Union[int, float] = 0) -> None:
        ready = not bool(delayed)
        if delayed:
            self._sequence += 1
            deadline = time.time() + delayed
            heapq.heappush(
                self._tasks_delayed,
                (deadline, self._sequence, func)
            )
        if ready:
            self._tasks_ready.append(func)

    def read_wait(self, fileno, func):
        self._read_waiting[fileno] = func

    def write_wait(self, fileno, func):
        self._write_waiting[fileno] = func

    def run(self) -> None:

        while (
                self._tasks_ready
                or self._tasks_delayed
                or self._read_waiting
                or self._write_waiting
        ):

            if not self._tasks_ready:
                if self._tasks_delayed:
                    deadline, _, task = self._tasks_delayed[0]
                    timeout = deadline - time.time()
                    if timeout < 0:
                        timeout = 0
                if not self._tasks_delayed:
                    timeout = None
                can_read, can_write, _ = select.select(
                    self._read_waiting,
                    self._write_waiting,
                    [],
                    timeout
                )
                for file_descriptor in can_read:
                    self._tasks_ready.append(self._read_waiting.pop(file_descriptor))
                for file_descriptor in can_write:
                    self._tasks_ready.append(self._write_waiting.pop(file_descriptor))

                now = time.time()
                while self._tasks_delayed:
                    if now < self._tasks_delayed[0][0]:
                        break
                    self._tasks_ready.append(heapq.heappop(self._tasks_delayed)[2])

            while self._tasks_ready:
                task = self._tasks_ready.popleft()
                task()

    def add_task(self, coro: Coroutine[Any, Any, Any]) -> None:
        self._tasks_ready.append(Task(coro))

    @staticmethod
    def switch() -> Awaitable:
        return Awaitable()

    async def sleep(self, delay):
        print(f'Sleeping {delay} sec. for single post write operation,'
              f'not blocking the server')
        self.call_soon(
            func=self._current,
            delayed=delay
        )
        self._current = None
        await self.switch()

    async def recv(self, sock: socket.socket):
        self.read_wait(sock, self._current)
        self._current = None
        await self.switch()
        return sock.recv(MAX_BYTES)

    async def send(self, sock, data):
        self.write_wait(sock, self._current)
        self._current = None
        await self.switch()
        return sock.send(data)

    async def accept(self, sock):
        self.read_wait(sock, self._current)
        self._current = None
        await self.switch()
        return sock.accept()


scheduler = Scheduler()


class Task:

    def __init__(self, coro: Coroutine[Any, Any, Any]):
        self._coro = coro

    def __call__(self):
        try:
            scheduler.set_current(self)
            self._coro.send(None)
            if scheduler.get_current():
                scheduler.add_to_tasks_ready(self)

        except (StopIteration,):
            pass
