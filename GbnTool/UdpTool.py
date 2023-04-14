from GbnTool import socket, threading, errno
from GbnTool.AddrTool import MACAddress
from GbnTool.ConfigTool import GbnConfig
from GbnTool.ErrorTool import CRCError
from GbnTool.FileTool import FileWriter, FileReader
from GbnTool.FrameTool import AckFrame, FrameFactory, GbnWindows
from GbnTool.LogTool import GbnLog

# 存储接收线程接收到的ack包，交给发送线程移动窗口
ack_get_dict = {}
ack_get_dict_lock = threading.Lock()


class UDPCommunication:
    def __init__(self, bind_port: int):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_port:
            self.udp_socket.bind(("", bind_port))
        print(f"[INFO] UDP socket bind to port: {bind_port}.")
        self.udp_socket.setblocking(False)
        self.dest_addr = None
        self.dest_port = None
        self.send_count = 0
        self.receive_count = 0

    def set_dest(self, dest_addr: str, dest_port: int):
        self.dest_addr = dest_addr
        self.dest_port = dest_port
        print(f"[INFO] Destination IP: {dest_addr}:{dest_port}.")

    @classmethod
    def bind(cls, bind_addr=None):
        return cls(bind_addr)

    def send(self, send_data: bytes):
        self.udp_socket.sendto(send_data, (self.dest_addr, self.dest_port))
        self.send_count += 1

    def receive(self, buf_size: int = (128 + GbnConfig.DATA_SIZE + GbnConfig.SEQ_BIT_SIZE * 2)):
        try:
            rec_data, rec_addr = self.udp_socket.recvfrom(buf_size)
        except socket.error as e:
            if e.errno != errno.EWOULDBLOCK:
                raise e
            return None, None
        else:
            self.receive_count += 1
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
        print("[INFO] Receive Thread start listening...")
        ack_dict = {}
        write_handle = FileWriter()
        while not self._stop_event.is_set():
            rec_data, rec_addr = self.udp_handle.receive()
            if rec_addr is None and rec_data is None:
                continue
            # 检查CRC纠错码
            try:
                print(rec_data)
                rec_frame = FrameFactory.from_bytes(rec_data)
            except CRCError:
                GbnLog.receive_log(self.udp_handle.receive_count, -1, -1, "DataErr", "ReceiveError")
                continue

            # 若非发给本机的包，跳过
            if rec_frame.dst_mac_addr != GbnConfig.MAC_ADDRESS:
                GbnLog.receive_log(self.udp_handle.receive_count, -1, -1, "AddrErr", "ReceiveError")
                continue
            # 若为数据帧
            if rec_frame.DATA_FRAME:
                # 若第一次接收包，登记入接收map中
                if rec_frame.src_mac_addr not in ack_dict:
                    ack_dict[rec_frame.src_mac_addr] = GbnConfig.INIT_SEQ_NO
                # 若接收到的包与要接收的序号相同
                if rec_frame.seq_num == ack_dict[rec_frame.src_mac_addr]:
                    print(rec_frame.seq_num)
                    ack_dict[rec_frame.src_mac_addr] = (ack_dict[rec_frame.src_mac_addr] + 1) % (GbnConfig.SW_SIZE + 1)
                    result = write_handle.write(rec_frame.payload)
                    GbnLog.receive_log(self.udp_handle.receive_count, rec_frame.seq_num, rec_frame.seq_num)
                    ack_frame = AckFrame(src_mac=GbnConfig.MAC_ADDRESS, dst_mac=rec_frame.src_mac_addr,
                                         ack_num=rec_frame.seq_num)
                    # 发送确认帧
                    self.udp_handle.send(ack_frame.frame_bytes)
                else:
                    GbnLog.receive_log(self.udp_handle.receive_count, ack_dict[rec_frame.src_mac_addr],
                                       rec_frame.seq_num, "NoErr")
                if rec_frame.payload == GbnConfig.FILE_END_FLAG:
                    ack_dict.pop(rec_frame.src_mac_addr)
            # 若为确认帧
            else:
                GbnLog.receive_log(self.udp_handle.receive_count, -1, rec_frame.seq_num, "OK", "ReceiveACK")
                with ack_get_dict_lock:
                    ack_get_dict[rec_frame.src_mac_addr] = rec_frame.seq_num

        print('Thread stopped')


class SendThread:
    def __init__(self, udp_handle: UDPCommunication):
        self.window = None
        self.ack_send_dict = None
        self.udp_handle = udp_handle
        self.rec_thread = ReceiveThread(udp_handle)

    def run(self) -> int:
        self.rec_thread.start()
        while True:
            self.udp_handle.send_count = 0
            with ack_get_dict_lock:
                ack_get_dict.clear()
            message = input("[INPUT] Please input the destination MAC address , or input 0 to exit:")
            if message == '0':
                self.rec_thread.stop()
                self.rec_thread.join()
                return 0
            try:
                dst_mac = MACAddress.from_str(message)
            except ValueError:
                print("[WARNING] Invalid Mac Address")
                continue
            self.window = GbnWindows(dst_mac)

            message = input("[INPUT] Please input the file to send , or input 0 to exit:")
            if message == '0':
                self.rec_thread.stop()
                self.rec_thread.join()
                return 0
            try:
                file_handle = FileReader(message)
            except FileNotFoundError:
                print("[WARNING] Invalid File Name.")
                continue
            self.window.bind_file(file_handle)
            seq = self.window.begin_point

            while not self.window.if_end:
                # 判断ack表，移动窗口
                with ack_get_dict_lock:
                    ack_get = ack_get_dict.copy()
                for key, value in ack_get.items():
                    if key == dst_mac:
                        self.window.slide(value)
                        with ack_get_dict_lock:
                            ack_get_dict.pop(key)
                # 超时
                if not self.window.check():
                    seq = self.window.begin_point
                if seq == self.window.unused_point:
                    continue
                # 发送数据帧
                if self.window.get_data(seq) != b"":
                    print(self.window.get_data(seq))
                    self.udp_handle.send(self.window.get_data(seq))
                    GbnLog.send_log(self.udp_handle.send_count, seq,
                                    self.window.get_status(seq), self.window.unused_point)
                    self.window.set_status(seq)
                    self.window.start_timing(seq)
                    seq = (seq + 1) % (GbnConfig.SW_SIZE + 1)

            print("_______________")
            tmp_end_flag = False
            while True:
                with ack_get_dict_lock:
                    ack_get = ack_get_dict.copy()
                for key, value in ack_get.items():
                    if key == dst_mac:
                        if value == (self.window.file_end_point + GbnConfig.SW_SIZE) % (GbnConfig.SW_SIZE + 1):
                            print(f"[INFO] File:{message} Send Finish!")
                            tmp_end_flag = True
                            break
                        self.window.slide(value)
                        with ack_get_dict_lock:
                            ack_get_dict.pop(key)
                if tmp_end_flag:
                    break
                # 超时
                if not self.window.check():
                    seq = self.window.begin_point
                if seq == self.window.unused_point:
                    continue
                # 发送数据帧

                # TODO:
                if self.window.get_data(seq) != b"":
                    print(self.window.get_data(seq))
                    self.udp_handle.send(self.window.get_data(seq))
                    GbnLog.send_log(self.udp_handle.send_count, seq,
                                    self.window.get_status(seq), self.window.unused_point)
                    self.window.set_status(seq)
                    self.window.start_timing(seq)
                    seq = (seq + 1) % (GbnConfig.SW_SIZE + 1)
