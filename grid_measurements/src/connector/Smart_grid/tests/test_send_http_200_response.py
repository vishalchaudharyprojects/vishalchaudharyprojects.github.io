import unittest
from unittest.mock import Mock
from grid_measurements.src.connector.Smart_grid.functions.sm.send_http_200_response import send_http_200_response

class test_send_http_200_response(unittest.TestCase):
    def test_response_without_body(self):
        # Mock-Socket erstellen
        mock_sock = Mock()

        # Funktion aufrufen
        send_http_200_response(mock_sock)

        # Erwartete Header ohne Body
        expected_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
        ).encode('utf-8')

        # Überprüfen, ob nur die Header gesendet wurden
        mock_sock.sendall.assert_called_once_with(expected_headers)

if __name__ == "__main__":
    unittest.main()
