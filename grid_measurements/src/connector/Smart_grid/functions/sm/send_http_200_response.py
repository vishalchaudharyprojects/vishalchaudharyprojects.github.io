def send_http_200_response(sock, body=None):
    """
    This function sends an HTTP 200 response to the client to acknowledge the messagte.

    :param sock: The socket to send the response to.
    :param body: Optional body to include in the response.
    :return: None
    """
    # Step 1: Construct the HTTP 200 response headers
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"  # Adjust Content-Type as needed
    )

    # Step 2: If there is a body, include Content-Length in headers
    if body:
        response_headers += f"Content-Length: {len(body)}\r\n"
    response_headers += "\r\n"  # End of headers section

    # Step 3: Send the headers
    sock.sendall(response_headers.encode('utf-8'))

    # Step 4: Send the body if provided
    if body:
        sock.sendall(body)
