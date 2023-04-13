from GbnTool import socket


class UDPCommunication:
    def __init__(self, bind_addr=None):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_addr:
            self.udp_socket.bind(("", bind_addr))

    @classmethod
    def bind(cls, bind_addr=None):
        return cls(bind_addr)

    def send(self, send_data, dest_addr: str, dest_port: int):
        self.udp_socket.sendto(send_data.encode(), (dest_addr, dest_port))

    def receive(self, buf_size=1024):
        rec_data, rec_addr = self.udp_socket.recvfrom(buf_size)
        return rec_data.decode(), rec_addr

    def close(self):
        self.udp_socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.udp_socket.close()

    def __del__(self):
        self.udp_socket.close()


if __name__ == "__main__":
    with UDPCommunication.bind(8888) as u:
        data, addr = u.receive()
        print(data)
