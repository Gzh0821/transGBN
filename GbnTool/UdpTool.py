import errno
import queue

from GbnTool import socket, threading
from GbnTool.ErrorTool import CRCError
from GbnTool.FileTool import FileWriter
from GbnTool.FrameTool import GbnFrame
from GbnTool.configTool import GbnConfig

wait_queue = queue.Queue()


class UDPCommunication:
    def __init__(self, bind_addr=None):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_addr:
            self.udp_socket.bind(("", bind_addr))
        self.udp_socket.setblocking(False)

    @classmethod
    def bind(cls, bind_addr=None):
        return cls(bind_addr)

    def send(self, send_data: bytes, dest_addr: str, dest_port: int):
        self.udp_socket.sendto(send_data, (dest_addr, dest_port))

    def receive(self, buf_size: int = (128 + GbnConfig.DATA_SIZE + GbnConfig.SEQ_BIT_SIZE * 2)):
        try:
            rec_data, rec_addr = self.udp_socket.recvfrom(buf_size)
        except socket.error as e:
            if e.errno != errno.EWOULDBLOCK:
                raise e
            return None, None
        else:
            return rec_data, rec_addr

    def close(self):
        self.udp_socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.udp_socket:
            self.udp_socket.close()

    def __del__(self):
        if self.udp_socket:
            self.udp_socket.close()


class ReceiveThread(threading.Thread):
    def __init__(self, udp_handle: UDPCommunication):
        super(ReceiveThread, self).__init__()
        self.udp_handle = udp_handle
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        ack_dict = {}
        write_handle = FileWriter()
        while not self._stop_event.is_set():
            rec_data, rec_addr = self.udp_handle.receive()
            if rec_addr is None and rec_data is None:
                continue
            try:
                rec_frame = GbnFrame.from_bytes(rec_data)
            except CRCError:
                continue
            if rec_frame.dst_mac_addr != GbnConfig.MAC_ADDRESS:
                continue
            if rec_frame.src_mac_addr not in ack_dict:
                ack_dict[rec_frame.src_mac_addr] = GbnConfig.INIT_SEQ_NO
            if rec_frame.seq_num == ack_dict[rec_frame.src_mac_addr]:
                ack_dict[rec_frame.src_mac_addr] = (ack_dict[rec_frame.src_mac_addr] + 1) % (GbnConfig.SW_SIZE + 1)
                wait_queue.put((rec_frame.src_mac, rec_frame.seq_num))
                result = write_handle.write(rec_frame.payload)
                if result:
                    write_handle.reset()
        print('Thread stopped')


class SendThread:
    def __init__(self, udp_handle: UDPCommunication):
        self.udp_handle = udp_handle
        self.rec_thread = ReceiveThread(udp_handle)

    def run(self) -> int:
        self.rec_thread.start()
        while True:
            message = input("[INPUT] Please input the destination MAC address , or input 0 to exit:")
            if message == '0':
                self.rec_thread.stop()
                self.rec_thread.join()
                return 0
