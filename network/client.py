import socket
import time

INITIAL_TIMEOUT = 15
SERVER_TURN_TIMEOUT = 30


class Client:
    def __init__(self, port_number: int) -> None:
        self.port_number = port_number
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_file = self.socket.makefile()
        self.connected = False

    def connect(self):
        start = time.time()
        while not self.connected:
            if time.time() - start > INITIAL_TIMEOUT:
                raise RuntimeError(
                    f"Timeout when trying to connect to engine at {self.port_number}"
                )
            address = (
                "127.0.0.1",
                self.port_number,
            )

            try:
                self.socket.connect(address)
                self.connected = True
            except ConnectionRefusedError:
                time.sleep(1)

    def read(self) -> str:
        self.socket.settimeout(SERVER_TURN_TIMEOUT)
        data = self.socket_file.readline().strip()

        return data

    def write(self, message: str) -> None:
        self.socket.settimeout(SERVER_TURN_TIMEOUT)
        self.socket.sendall(str.encode(message + "\n"))

    def disconnect(self):
        self.socket.close()
        self.connected = False
