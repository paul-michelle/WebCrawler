import format_utils
import settings
import http.server
import re
import socketserver
import json

PORT = 8087
CONTENT_TYPE = 'application/json; charset=utf-8'
PATH = settings.TARGET_DIR_PATH
UUID_LENGTH = 32


class RedditHTTPHandler(http.server.SimpleHTTPRequestHandler):

    def get_id(self):
        unique_id_in_url = re.search('/posts/[\w]*/', self.path)
        if unique_id_in_url:
            unique_id = unique_id_in_url.group().split('/')[2]
            if len(unique_id) != UUID_LENGTH:
                self.send_response(404, 'Inadequate unique_id length. 32 chars expected')
                self.end_headers()
                return
            return unique_id

    def do_GET(self) -> None:
        if self.path == '/posts/':
            with open(file=PATH, mode='r') as f:
                already_written_lines = f.readlines()
            response_text = [format_utils.inline_values_to_dict(line) for line in already_written_lines]
            response_body = json.dumps(response_text).encode('utf-8')
            self.send_response(200, 'OK')
            self.send_header('Content-Type', CONTENT_TYPE)
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
            return

        valid_id_given = self.get_id()
        if valid_id_given:
            with open(PATH, 'r') as f:
                already_written_lines = f.readlines()
            for line in already_written_lines:
                if line.startswith(valid_id_given):
                    response_text = format_utils.inline_values_to_dict(line)
                    response_body = json.dumps(response_text).encode('utf-8')
                    self.send_response(200, 'OK')
                    self.send_header('Content-Type', CONTENT_TYPE)
                    self.send_header('Content-Length', str(len(response_body)))
                    self.end_headers()
                    self.wfile.write(response_body)
                    return
            self.send_response(404, 'Not found in your txt-file')
            self.end_headers()

    def do_DELETE(self) -> None:
        valid_id_given = self.get_id()
        if valid_id_given:
            with open(PATH, 'r+') as f:
                already_written_lines = f.readlines()
                f.seek(0)
                for line in already_written_lines:
                    if not line.startswith(valid_id_given):
                        f.write(line)
                f.truncate()
                f.seek(0)
                if len(f.readlines()) == len(already_written_lines):
                    self.send_response(404, 'Not found in your txt-file')
                    self.end_headers()
                    return
            self.send_response(204, 'Post deleted')
            self.end_headers()

    def do_POST(self):
        pass

    def do_PUT(self):
        pass


def main():
    with socketserver.TCPServer(server_address=('localhost', PORT),
                                RequestHandlerClass=RedditHTTPHandler) as httpd:
        print(f'Serving at port {PORT}')
        httpd.serve_forever()


if __name__ == '__main__':
    main()
