import socket
import re
import os
import logging
from urllib.parse import urlparse, parse_qs

HTTP___ = rb'([A-Z]+) +(/.*) +HTTP/1.1'
RECEIVE = 1024
NOT_FOUND_JPG = 'not_found.jpg'

INDEX_HTML = 'index.html'

ERROR_JPG = 'error.jpg'

FORBIDDEN_JPG = 'forbidden.jpg'

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/lucky.log'

EMPTY = ''
EMPTY1 = '/'
RB = 'rb'
JPG = 'jpg'


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
HTTP_400_BAD_REQUEST = b'HTTP/1.1 400 Bad Request\r\n'

# HTTP Headers
CONTENT_TYPE_HEADER = b'Content-Type: '
CONTENT_LENGTH_HEADER = b'Content-Length: '

# File Extensions and Content Types
FILE_EXTENSIONS = {
    'html': 'text/html;charset=utf-8',
    JPG: 'image/jpeg',
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
URI_UPLOAD = '/upload'
URI_IMAGE = '/image?'
URI_CALCULATE_NEXT = '/calculate-next?'
URI_CALCULATE_AREA = '/calculate-area?'
URI_INDEX = '/index.html'


UPLOAD_PATH = '/Users/iftach_1kasorla/Documents/4.0/upload'
ERR_BAD_REQUEST = b"HTTP/1.1 400 Bad Request\r\n\r\nBad Request: Invalid upload request"

# ... (previous code remains unchanged)


def handle_client_request(client_resource, client_socket):
    """
    Handles client requests based on the requested resource.

    Args:
    - resource (str): The requested resource.
    - client_socket (socket object): The client socket object.

    Returns:
    - None
    """
    logging.info(f"Handling request for {client_resource}")

    if client_resource == EMPTY1 or client_resource == EMPTY:
        uri = DEFAULT_URL
    else:
        uri = client_resource

    # Check if the request method is POST
    if uri.startswith(URI_UPLOAD):
        upload(client_resource, client_socket, EMPTY)
        return
    elif uri.startswith(URI_IMAGE):
        handle_image_request(uri, client_socket)
        return

    if uri.startswith(URI_CALCULATE_NEXT):
        # Parse the query string to extract the 'num' parameter
        query_params = parse_qs(urlparse(uri).query)
        num_param = query_params.get('num', [EMPTY])

        if not num_param:
            # 'num' parameter not provided in the query string, return 400 Bad Request
            error_response = HTTP_400_BAD_REQUEST + b'\r\nBad Request: Missing "num" parameter'
            client_socket.sendall(error_response)
            return

        try:
            num = int(num_param[0])
            next_num = num + 1
            response_content = f'The next number after {num} is {next_num}'.encode('utf-8')

            content_type = CONTENT_TYPE_HEADER + b'text/plain;charset=utf-8\r\n'
            content_length_header = CONTENT_LENGTH_HEADER + str(len(response_content)).encode() + b'\r\n'
            response = HTTP_200_OK + content_type + content_length_header + b'\r\n' + response_content

            client_socket.sendall(response)
        except ValueError:
            # Handle the case where 'num' is not a valid integer
            error_response = HTTP_400_BAD_REQUEST + b'\r\nBad Request: Invalid "num" parameter'
            client_socket.sendall(error_response)
        return

    if uri.startswith(URI_CALCULATE_AREA):
        # Parse the query string to extract the 'height' and 'width' parameters
        query_params = parse_qs(urlparse(uri).query)
        height_param = query_params.get('height', [EMPTY])
        width_param = query_params.get('width', [EMPTY])

        if not height_param or not width_param:
            # 'height' or 'width' parameter is missing in the query string, return 400 Bad Request
            error_response = HTTP_400_BAD_REQUEST + b'\r\nBad Request: Missing "height" or "width" parameter'
            client_socket.sendall(error_response)
            return

        try:
            height = float(height_param[0])
            width = float(width_param[0])
            area = (height * width) / 2
            response_content = f'The area is: {area}'.encode('utf-8')

            content_type = CONTENT_TYPE_HEADER + b'text/plain;charset=utf-8\r\n'
            content_length_header = CONTENT_LENGTH_HEADER + str(len(response_content)).encode() + b'\r\n'
            response = HTTP_200_OK + content_type + content_length_header + b'\r\n' + response_content

            client_socket.sendall(response)
        except ValueError:
            # Handle the case where 'height' or 'width' is not a valid float
            error_response = HTTP_400_BAD_REQUEST + b'\r\nBad Request: Invalid "height" or "width" parameter'
            client_socket.sendall(error_response)
        return

    try:
        if uri == URI_FORBIDDEN:
            forbidden_img_filename = FORBIDDEN_JPG  # Change '/path/to/forbidden.jpg' to the actual path of your forbidden image
            with open(forbidden_img_filename, RB) as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)
            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_403_FORBIDDEN + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)
        elif uri == URI_ERROR:
            error_img_filename = ERROR_JPG  # Change '/path/to/error.jpg' to the actual path of your error image
            with open(error_img_filename, RB) as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)
            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_500_INTERNAL_ERROR + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)
        elif uri == URI_MOVED:
            logging.info("URI Moved requested")
            response = HTTP_302_TEMP_REDIRECT + b'Location: /index.html\r\n\r\n'
            client_socket.sendall(response)
            # Change the requested resource to '/index.html'
            handle_client_request(EMPTY1, client_socket)
            return
        else:
            # Handle other URIs and serve files from the WEBROOT directory
            filename = os.path.join(WEBROOT, uri.strip(EMPTY1))
            if os.path.isdir(filename):
                filename = os.path.join(filename, INDEX_HTML)
            file_extension = filename.split('.')[-1]

            with open(filename, RB) as file:
                data = file.read()
                content_length = len(data)

            content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(file_extension, b'text/plain').encode() + b'\r\n'
            content_length_header = CONTENT_LENGTH_HEADER + str(content_length).encode() + b'\r\n'
            response = HTTP_200_OK + content_type + content_length_header + b'\r\n' + data
            client_socket.sendall(response)
    except FileNotFoundError:
        # For 404 Not Found, serve an image from outside the WEBROOT directory
        not_found_img_filename = NOT_FOUND_JPG  # Change '/path/to/not_found.jpg' to the actual path of your not found image
        with open(not_found_img_filename, RB) as img_file:
            img_data = img_file.read()
            img_content_length = len(img_data)
        img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
        img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
        img_response = HTTP_404_NOT_FOUND + img_content_type + img_content_length_header + b'\r\n' + img_data
        client_socket.sendall(img_response)
    except Exception as e:
        logging.error(f"Error handling file: {str(e)}")
        # For other errors, serve an image from outside the WEBROOT directory
        server_error_img_filename = ERROR_JPG  # Change '/path/to/server_error.jpg' to the actual path of your server error image
        with open(server_error_img_filename, RB) as img_file:
            img_data = img_file.read()
            img_content_length = len(img_data)
        img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
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
        return False, EMPTY, EMPTY

    match = re.match(HTTP___, request)

    if not match:
        return False, EMPTY, EMPTY

    method = match.group(1).decode()
    my_resource = match.group(2).decode()

    if method == 'GET' or method == 'POST':
        return True, my_resource, method

    return False, EMPTY, method


def handle_client(client_socket):
    """
    Handles the client's connection, receiving and processing requests.

    Args:
    - client_socket (socket object): The client socket object.

    Returns:
    - None
    """
    try:
        client_request = client_socket.recv(RECEIVE)
        while True:
            if b'\r\n\r\n' in client_request:
                break
            client_request += client_socket.recv(RECEIVE)

        if not client_request:
            return

        valid_http, valid_resource, method = validate_http_request(client_request)

        if valid_http:
            if method == 'GET':
                handle_client_request(valid_resource, client_socket)
            elif method == 'POST':
                handle_post_request(valid_resource, client_socket, client_request)
            else:
                logging.error('Error: Unsupported HTTP method')
        else:
            logging.error('Error: Not a valid HTTP request')

    except socket.timeout:
        logging.warning('Connection timed out')
    except socket.error as e:
        logging.error(f'Socket error: {e}')
    finally:
        logging.info('Closing connection')
        client_socket.close()


def handle_post_request(post_resource, client_socket, request_data):
    """
    Handles POST requests.

    Args:
    - resource (str): The requested resource.
    - client_socket (socket object): The client socket object.
    - request_data (bytes): The data received in the POST request.

    Returns:
    - None
    """
    if post_resource.startswith(URI_UPLOAD):
        # Extract the content length from the request headers
        content_length_match = re.search(rb'Content-Length: (\d+)', request_data)
        if content_length_match:
            content_length = int(content_length_match.group(1))
        else:
            logging.error('Error: Content-Length not found in POST request')
            return

        # Extract the request body based on the content length
        request_body = b''
        while len(request_body) < content_length:
            chunk = client_socket.recv(RECEIVE)
            if not chunk:
                break
            request_body += chunk

        if len(request_body) < content_length:
            logging.error('Error: Incomplete request body received')
            return

        # Call the upload function with the resource and request body
        upload(post_resource, client_socket, request_body)


def handle_image_request(uri, client_socket):
    """
    Handles the client's image request.

    Args:
    - uri (bytes): The URI containing the image request parameters.
    - client_socket (socket object): The client socket object.

    Returns:
    - None

    The function processes the image request, extracts the image name parameter, and sends the corresponding image
    content as the HTTP response to the client socket. If the image is not found, a default image is served.
    """
    try:
        # Parse the query string to extract the 'image-name' parameter
        query_params = parse_qs(urlparse(uri).query)
        name_image_param = query_params.get('image-name', [EMPTY])

        # Log information for debugging
        logging.debug(f"Query Parameters: {query_params}")
        logging.debug(f"Extracted image-name parameter: {name_image_param}")

        if not name_image_param or not name_image_param[0]:
            # 'image-name' parameter not provided or empty, return 400 Bad Request
            error_response = HTTP_400_BAD_REQUEST + b'\r\nBad Request: Missing or empty "image-name" parameter'
            client_socket.sendall(error_response)
            return

        try:
            # Extract the requested image file name
            image_filename = name_image_param[0]

            # Log information for debugging
            logging.debug(f"Requested image filename: {image_filename}")

            # Combine folder and file name
            full_image_path = os.path.join(UPLOAD_PATH, image_filename)

            # Log information for debugging
            logging.debug(f"Full image path: {full_image_path}")

            # Read the image file
            with open(full_image_path, RB) as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)

            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_200_OK + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)

        except FileNotFoundError:
            # For 404 Not Found, serve an image from outside the WEBROOT directory
            not_found_img_filename = NOT_FOUND_JPG  # Change '/path/to/not_found.jpg' to the actual path of your not found image
            with open(not_found_img_filename, RB) as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)

            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_404_NOT_FOUND + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)

        except Exception as e:
            logging.error(f"Error handling image request: {str(e)}")
            # For other errors, serve an image from outside the WEBROOT directory
            server_error_img_filename = ERROR_JPG  # Change '/path/to/server_error.jpg' to the actual path of your server error image
            with open(server_error_img_filename, RB) as img_file:
                img_data = img_file.read()
                img_content_length = len(img_data)

            img_content_type = CONTENT_TYPE_HEADER + FILE_EXTENSIONS.get(JPG, b'image/jpeg').encode() + b'\r\n'
            img_content_length_header = CONTENT_LENGTH_HEADER + str(img_content_length).encode() + b'\r\n'
            img_response = HTTP_500_INTERNAL_ERROR + img_content_type + img_content_length_header + b'\r\n' + img_data
            client_socket.sendall(img_response)

    except Exception as e:
        logging.error(f"Error handling image request: {str(e)}")


def upload(upload_resource, client_socket, request_body):
    """
    Handles the client's file upload request.

    Args:
    - upload_resource (bytes): The resource path for the file upload.
    - client_socket (socket object): The client socket object.
    - request_body (bytes): The data received in the file upload request.

    Returns:
    - None

    The function extracts the file name from the upload resource, combines it with the upload path, and writes the
    received request body to the specified file. It then sends an HTTP response to the client indicating the success
    or failure of the upload.
    """
    try:
        # Extract the file name from the resource (assuming resource contains 'file-name=')
        start_name = upload_resource.find('=')
        file_name = upload_resource[start_name + 1:]

        # Combine folder and file name
        full_file_path = os.path.join(UPLOAD_PATH, file_name)

        # Write the request body to the file
        with open(full_file_path, "wb") as file:
            file.write(request_body)

        success_response = b"HTTP/1.1 200 OK\r\n\r\nUpload successful"
        client_socket.sendall(success_response)
    except Exception as e:
        # Send 400 bad request
        client_socket.sendall(ERR_BAD_REQUEST)
        logging.debug(f"Error handling upload: {str(e)}")
    finally:
        return


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
    # Asserts for constants' types

    assert isinstance(RECEIVE, int), "RECEIVE should be an integer"
    assert isinstance(DEFAULT_URL, str), "DEFAULT_URL should be a string"
    assert isinstance(QUEUE_SIZE, int), "QUEUE_SIZE should be an integer"
    assert isinstance(IP, str), "IP should be a string"
    assert isinstance(PORT, int), "PORT should be an integer"
    assert isinstance(SOCKET_TIMEOUT, int), "SOCKET_TIMEOUT should be an integer"
    assert isinstance(REDIRECTION_DICTIONARY, dict), "REDIRECTION_DICTIONARY should be a dictionary"
    assert isinstance(WEBROOT, str), "WEBROOT should be a string"
    assert isinstance(LOG_FORMAT, str), "LOG_FORMAT should be a string"
    assert isinstance(LOG_LEVEL, int), "LOG_LEVEL should be an integer"
    assert isinstance(LOG_DIR, str), "LOG_DIR should be a string"
    assert isinstance(LOG_FILE, str), "LOG_FILE should be a string"
    assert isinstance(EMPTY, str), "EMPTY should be a string"
    assert isinstance(NOT_FOUND_JPG, str), "NOT_FOUND_JPG should be a string"
    assert isinstance(ERROR_JPG, str), "ERROR_JPG should be a string"
    assert isinstance(FORBIDDEN_JPG, str), "FORBIDDEN_JPG should be a string"

    # Test the validate_http_request function
    sample_request = b'GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n'
    sample_request1 = b'GET/index.htmlHTTP/1.1\r\nHost: localhost\r\n\r\n'
    valid, resource, method1 = validate_http_request(sample_request)
    valid1, resource1, method2 = validate_http_request(sample_request1)
    sample_post_request = b'POST /upload?file-name=test.txt HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nHello'
    valid_post, resource_post, method_post = validate_http_request(sample_post_request)

    # Assert the function output matches the expected result
    assert not valid1
    assert valid, "Expected a valid HTTP request"
    assert resource == '/index.html', "Expected resource '/index.html'"
    assert valid_post, "Expected a valid POST request"
    assert resource_post == '/upload?file-name=test.txt', "Expected resource '/upload?file-name=test.txt'"
    assert method_post == 'POST', "Expected HTTP method 'POST'"

    # Start logging and the server
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    logging.info("Starting the server...")
    logging.debug(f"Using {LOG_LEVEL} level logging")
    main()
