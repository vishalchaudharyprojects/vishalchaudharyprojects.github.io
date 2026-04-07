def parse_http_post(data: bytes) -> bytes:
    """
    This function parses the HTTP POST request and returns the body of the request

    :param: data -> bytestring
    :return: body -> string
    """
    # Split HTTP headers from body
    headers, body = data.split(b'\r\n\r\n', 1)

    # Decode headers (for inspection)
    headers_str = headers.decode('utf-8')
    print("Headers:")
    print(headers_str)

    # The body starts after the headers
    print("\nBody (binary data):")
    print(body[:100])  # Print first 100 bytes for inspection

    return headers_str, body
