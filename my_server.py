import socket
import re
import os
import logging

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/lucky.log'

# Create the log directory if it doesn't exist
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)

DEFAULT_URL = '/index.html'
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
REDIRECTION_DICTIONARY = {'/about': '/about.html'}
WEBROOT = r'/Users/iftach_1kasorla/Documents/4.0/WEB-ROOT'

# HTTP Status Codes
HTTP_200_OK = b'HTTP/1.1 200 OK\r\n'
HTTP_302_FOUND = b'HTTP/1.1 302 Found\r\n'
HTTP_302_TEMP_REDIRECT = b'HTTP/1.1 302 TEMPORARY REDIRECT\r\n'
HTTP_403_FORBIDDEN = b'HTTP/1.1 403 Forbidden\r\n'
HTTP_404_NOT_FOUND = b'HTTP/1.1 404 Not Found\r\n'
HTTP_500_INTERNAL_ERROR = b'HTTP/1.1 500 Internal Server Error\r\n'

# HTTP Headers
CONTENT_TYPE_HEADER = b'Content-Type: '
CONTENT_LENGTH_HEADER = b'Content-Length: '

# File Extensions and Content Types
FILE_EXTENSIONS = {
    'html': 'text/html;charset=utf-8',
    'jpg': 'image/jpeg',
    'css': 'text/css',
    'js': 'text/javascript; charset=UTF-8',
    'txt': 'text/plain',
    'ico': 'image/x-icon',
    'gif': 'image/jpeg',
    'png': 'image/png'
}

# URIs
URI_FORBIDDEN = '/forbidden'
URI_MOVED = '/moved'
URI_ERROR = '/error'


def handle_client_request(resource, client_socket):
    """
    Handles client requests based on the requested resource.

    Args:
    - resource (str): The requested resource.
    - client_socket (socket object): The client socket object.

    Returns:
    - None
    """
    logging.info(f"Handling request for {resource}")

    if resource == '/' or resource == '':
        uri = DEFAULT_URL
    else:
        uri = resource

    try:
        if uri == URI_FORBIDDEN:
            forbidden_img_filename = os.path.join(WEBROOT, 'imgs', 'forbidden.jpg')  # Change 'forbidden.jpg' to your forbidden image name
            with open(forbidden_img_filename, 'rb') as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)
            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get('jpg', b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_403_FORBIDDEN + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)
        elif uri == URI_ERROR:
            error_img_filename = os.path.join(WEBROOT, 'imgs', 'error.jpg')  # Change 'error.jpg' to your error image name
            with open(error_img_filename, 'rb') as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)
            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get('jpg', b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_500_INTERNAL_ERROR + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)

        elif uri == URI_MOVED:
            logging.info("URI Moved requested")
            response = HTTP_302_TEMP_REDIRECT + b'Location: /index.html\r\n\r\n'
            client_socket.sendall(response)
            # Change the requested resource to '/index.html'
            handle_client_request('/', client_socket)
            return
        else:
            filename = os.path.join(WEBROOT, uri.strip('/'))
            if os.path.isdir(filename):
                filename = os.path.join(filename, 'index.html')
            file_extension = filename.split('.')[-1]

            with open(filename, 'rb') as file:
                data = file.read()
                content_length = len(data)

            content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(file_extension, b'text/plain').encode() + b'\r\n'
            content_length_header = CONTENT_LENGTH_HEADER + str(content_length).encode() + b'\r\n'
            response = HTTP_200_OK + content_type + content_length_header + b'\r\n' + data
            client_socket.sendall(response)
    except FileNotFoundError:
        not_found_img_filename = os.path.join(WEBROOT, 'imgs', 'not_found.jpg')  # Change 'not_found.jpg' to your not found image name
        with open(not_found_img_filename, 'rb') as img_file:
            img_data = img_file.read()
            img_content_length = len(img_data)
        img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get('jpg', b'image/jpeg').encode() + b'\r\n'
        img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
        img_response = HTTP_404_NOT_FOUND + img_content_type + img_content_length_header + b'\r\n' + img_data
        client_socket.sendall(img_response)
    except Exception as e:
        logging.error(f"Error handling file: {str(e)}")
        server_error_img_filename = os.path.join(WEBROOT, 'imgs', 'server_error.jpg')  # Change 'server_error.jpg' to your server error image name
        with open(server_error_img_filename, 'rb') as img_file:
            img_data = img_file.read()
            img_content_length = len(img_data)
        img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get('jpg', b'image/jpeg').encode() + b'\r\n'
        img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
        img_response = HTTP_500_INTERNAL_ERROR + img_content_type + img_content_length_header + b'\r\n' + img_data
        client_socket.sendall(img_response)



def validate_http_request(request):
    """
    Validates an incoming HTTP request.

    Args:
    - request (bytes): The HTTP request received from the client.

    Returns:
    - tuple: A tuple containing a boolean indicating whether the request is valid and the resource requested.
    """
    if not request:
        return False, ''

    match = re.match(rb'([A-Z]+) +(/.*) +HTTP/1.1', request)

    if not match:
        return False, ''

    method = match.group(1).decode()
    resource = match.group(2).decode()

    if method != 'GET':
        return False, ''

    return True, resource


def handle_client(client_socket):
    """
    Handles the client's connection, receiving and processing requests.

    Args:
    - client_socket (socket object): The client socket object.

    Returns:
    - None
    """
    while True:
        try:
            client_request = client_socket.recv(1024)
            while True:
                if b'\r\n\r\n' in client_request:
                    break
                client_request += client_socket.recv(1024)

            if not client_request:
                break

            valid_http, resource = validate_http_request(client_request)

            if valid_http:
                handle_client_request(resource, client_socket)
            else:
                logging.error('Error: Not a valid HTTP GET request')
                break

        except socket.timeout:
            logging.warning('Connection timed out')
            break

        except socket.error as e:
            logging.error(f'Socket error: {e}')
            break

    logging.info('Closing connection')
    client_socket.close()


def main():
    """
    Main function to start the server and handle incoming connections.

    Args:
    - None

    Returns:
    - None
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.info(f"Listening for connections on port {PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.info('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error(f'Received socket exception: {str(err)}')
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error(f'Received socket exception: {str(err)}')
    finally:
        server_socket.close()


if __name__ == "__main__":
    # Assertions for constants' types
    assert isinstance(DEFAULT_URL, str), "DEFAULT_URL should be a string"
    assert isinstance(QUEUE_SIZE, int), "QUEUE_SIZE should be an integer"
    assert isinstance(IP, str), "IP should be a string"
    assert isinstance(PORT, int), "PORT should be an integer"
    assert isinstance(SOCKET_TIMEOUT, int), "SOCKET_TIMEOUT should be an integer"
    assert isinstance(REDIRECTION_DICTIONARY, dict), "REDIRECTION_DICTIONARY should be a dictionary"
    assert isinstance(WEBROOT, str), "WEBROOT should be a string"

    # Start logging and the server
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    logging.info("Starting the server...")
    logging.debug(f"Using {LOG_LEVEL} level logging")
    main()
