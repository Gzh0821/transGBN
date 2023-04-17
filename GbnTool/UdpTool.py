#   Copyright 2023 Gaozih/Gzh0821 https://github.com/Gzh0821
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from GbnTool import socket, threading, errno
from GbnTool.AddrTool import MACAddress
from GbnTool.ConfigTool import GbnConfig
from GbnTool.ErrorTool import CRCError
from GbnTool.FileTool import FileWriter, FileReader
from GbnTool.FrameTool import AckFrame, FrameFactory, GbnWindows
from GbnTool.LogTool import GbnLog
from GbnTool.RandomTool import GbnRandom

# 存储接收线程接收到的ack包，交给发送线程移动窗口
ack_get_dict = {}
ack_get_dict_lock = threading.Lock()


class UDPCommunication:
    def __init__(self, bind_port: int):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_port:
            self.udp_socket.bind(("", bind_port))
        GbnConfig.print(f"[INFO] UDP socket bind to port: {bind_port}.")
        self.udp_socket.setblocking(False)
        self.dest_addr = None
        self.dest_port = None
        self.send_count = 0
        self.receive_count = 0

    def set_dest(self, dest_addr: str, dest_port: int):
        """
        Set the destination IP and port.
        :param dest_addr:
        :param dest_port:
        :return:
        """
        self.dest_addr = dest_addr
        self.dest_port = dest_port
        GbnConfig.print(f"[INFO] Destination IP: {dest_addr}:{dest_port}.")

    @classmethod
    def bind(cls, bind_addr=None):
        """
        Bind the UDP socket to a port.
        :param bind_addr:
        :return:
        """
        return cls(bind_addr)

    def send(self, send_data: bytes, error: bool = True, ack: bool = False):
        """
        Send data to the destination.
        :param send_data:
        :param error:
        :param ack:
        :return:
        """
        if error:
            # 依据概率参数随机产生位错误
            data = GbnRandom.random_error(send_data)
            if GbnRandom.keep():
                # 依据概率参数模拟送达或丢失
                self.udp_socket.sendto(data, (self.dest_addr, self.dest_port))
            if not ack:
                self.send_count += 1
        else:
            self.udp_socket.sendto(send_data, (self.dest_addr, self.dest_port))

    def receive(self, buf_size: int = (128 + GbnConfig.DATA_SIZE + GbnConfig.SEQ_BIT_SIZE * 2)):
        """
        Receive data from the destination.
        :param buf_size:
        :return:
        """
        try:
            rec_data, rec_addr = self.udp_socket.recvfrom(buf_size)
        except socket.error as e:
            if e.errno != errno.EWOULDBLOCK:
                raise e
            return None, None
        else:
            if rec_data[0] != GbnConfig.SYNC_FLAG[0]:
                self.receive_count += 1
            return rec_data, rec_addr

    def clear_send_count(self):
        """
        Clear the send count.
        :return:
        """
        self.send_count = 0

    def clear_receive_count(self):
        """
        Clear the reception count.
        :return:
        """
        self.receive_count = 0

    def close(self):
        """
        Close the UDP socket.
        :return:
        """
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
        """
        Initialize the reception thread.
        :param udp_handle:
        """
        super(ReceiveThread, self).__init__()
        self.udp_handle = udp_handle
        self._stop_event = threading.Event()

    def stop(self):
        """
        Stop the reception thread.
        :return:
        """
        self._stop_event.set()

    def run(self):
        """
        Run the reception thread.
        :return:
        """
        ack_dict = {}
        write_handle = FileWriter()
        GbnConfig.print("[INFO] Receive Thread start listening...")
        while not self._stop_event.is_set():
            rec_data, rec_addr = self.udp_handle.receive()
            if rec_addr is None and rec_data is None:
                continue
            if rec_data[0] == GbnConfig.SYNC_FLAG[0]:
                src = MACAddress.from_bytes(rec_data[1:7])
                dst = MACAddress.from_bytes(rec_data[7:13])
                if dst == GbnConfig.MAC_ADDRESS and src in ack_dict:
                    ack_dict.pop(src)
                    GbnConfig.print("[WARNING] Clear SEQ Number.")
                continue
            # 检查CRC纠错码
            try:
                # GbnConfig.print(rec_data)
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
                    # GbnConfig.print(rec_frame.seq_num)
                    ack_dict[rec_frame.src_mac_addr] = (ack_dict[rec_frame.src_mac_addr] + 1) % (GbnConfig.SW_SIZE + 1)
                    result, finish_flag = write_handle.write(rec_frame.payload)
                    GbnLog.receive_log(self.udp_handle.receive_count, rec_frame.seq_num, rec_frame.seq_num,
                                       pdu_count=result)
                    if finish_flag is not None:
                        GbnConfig.print(f"[INFO] file:{finish_flag} receive over!\n")
                        GbnLog.receive_done(self.udp_handle.receive_count, result, finish_flag, rec_frame.src_mac_addr)
                        self.udp_handle.clear_receive_count()
                    ack_frame = AckFrame(src_mac=GbnConfig.MAC_ADDRESS, dst_mac=rec_frame.src_mac_addr,
                                         ack_num=rec_frame.seq_num)
                    # 发送确认帧
                    self.udp_handle.send(ack_frame.frame_bytes, ack=True)
                else:
                    GbnLog.receive_log(self.udp_handle.receive_count, ack_dict[rec_frame.src_mac_addr],
                                       rec_frame.seq_num, "NoErr")
                    ack_frame = AckFrame(src_mac=GbnConfig.MAC_ADDRESS, dst_mac=rec_frame.src_mac_addr,
                                         ack_num=(ack_dict[rec_frame.src_mac_addr] + GbnConfig.SW_SIZE) % (
                                                 GbnConfig.SW_SIZE + 1))
                    self.udp_handle.send(ack_frame.frame_bytes, ack=True)
                    continue
                # if rec_frame.payload == GbnConfig.FILE_END_FLAG:
                #     ack_dict.pop(rec_frame.src_mac_addr)
            # 若为确认帧
            else:
                GbnLog.receive_log(self.udp_handle.receive_count, -1, rec_frame.seq_num, "OK", "ReceiveACK")
                with ack_get_dict_lock:
                    ack_get_dict[rec_frame.src_mac_addr] = rec_frame.seq_num

        GbnConfig.print('[INFO] Receive Thread stopped.')


class SendThread:
    def __init__(self, udp_handle: UDPCommunication):
        """
        Initialize the send thread.
        :param udp_handle:
        """
        self.window = None
        self.ack_send_dict = None
        self.udp_handle = udp_handle
        self.rec_thread = ReceiveThread(udp_handle)

    def run(self) -> int:
        """
        Run the send thread.
        :return:
        """
        self.rec_thread.start()
        while True:
            self.udp_handle.send_count = 0
            with ack_get_dict_lock:
                ack_get_dict.clear()
            if GbnConfig.DEST_MAC is None:
                message = input("[INPUT] Please input the destination MAC address , or input 0 to exit:")

                if message == '0':
                    self.rec_thread.stop()
                    self.rec_thread.join()
                    return 0
                try:
                    dst_mac = MACAddress.from_str(message)
                except ValueError:
                    GbnConfig.print("[WARNING] Invalid Mac Address!")
                    continue
            else:
                dst_mac = GbnConfig.DEST_MAC
                GbnConfig.print(f"[INFO] Destination MAC Address(from config):{str(dst_mac)}")
            self.window = GbnWindows(dst_mac)

            message = input("[INPUT] Please input the file to send , or input 0 to exit:")
            if message == '0':
                self.rec_thread.stop()
                self.rec_thread.join()
                return 0
            try:
                file_handle = FileReader(message)
            except FileNotFoundError:
                GbnConfig.print("[WARNING] Invalid File Name.")
                continue

            sync_byte: bytes = GbnConfig.SYNC_FLAG + GbnConfig.MAC_ADDRESS.to_bytes() + dst_mac.to_bytes()
            self.udp_handle.send(sync_byte, False)

            self.window.bind_file(file_handle)
            seq = self.window.begin_point
            while not self.window.if_end:
                # 判断ack表，移动窗口
                with ack_get_dict_lock:
                    ack_get = ack_get_dict.copy()
                for key, value in ack_get.items():
                    if key == dst_mac:
                        dis_1 = (seq + GbnConfig.SW_SIZE + 1 - self.window.unused_point) % (GbnConfig.SW_SIZE + 1)
                        dis_2 = (value + GbnConfig.SW_SIZE + 1 - self.window.unused_point) % (GbnConfig.SW_SIZE + 1)
                        self.window.slide(value)
                        # 若窗口滑动前seq在窗口中位置比ack靠前，则将seq置ack后一窗口位置
                        if not self.window.check() and dis_1 <= dis_2:
                            seq = self.window.begin_point
                        with ack_get_dict_lock:
                            ack_get_dict.pop(key)
                # 超时
                if not self.window.check():
                    # 将所有非超时重传置为RT
                    tmp_point = (self.window.begin_point + 1) % (GbnConfig.SW_SIZE + 1)
                    while tmp_point != seq:
                        self.window.set_status(tmp_point, "RT")
                        tmp_point = (tmp_point + 1) % (GbnConfig.SW_SIZE + 1)
                    seq = self.window.begin_point
                if seq == self.window.unused_point:
                    continue
                # 发送数据帧
                if not self.window.if_end or seq != self.window.file_end_point:
                    # GbnConfig.print(self.window.get_data(seq))
                    self.udp_handle.send(self.window.get_data(seq))
                    GbnLog.send_log(self.udp_handle.send_count, seq,
                                    self.window.get_status(seq), self.window.unused_point)
                    self.window.set_status(seq)
                    self.window.start_timing(seq)
                    seq = (seq + 1) % (GbnConfig.SW_SIZE + 1)

            # GbnConfig.print("_______________")
            tmp_end_flag = False
            while True:
                with ack_get_dict_lock:
                    ack_get = ack_get_dict.copy()
                for key, value in ack_get.items():
                    if key == dst_mac:
                        if value == (self.window.file_end_point + GbnConfig.SW_SIZE) % (GbnConfig.SW_SIZE + 1):
                            tmp_end_flag = True
                            break
                        dis_1 = (seq + GbnConfig.SW_SIZE + 1 - self.window.unused_point) % (GbnConfig.SW_SIZE + 1)
                        dis_2 = (value + GbnConfig.SW_SIZE + 1 - self.window.unused_point) % (GbnConfig.SW_SIZE + 1)
                        self.window.slide(value)
                        # 若窗口滑动前seq在窗口中位置比ack靠前，则将seq置ack后一窗口位置
                        if not self.window.check() and dis_1 <= dis_2:
                            seq = self.window.begin_point
                        with ack_get_dict_lock:
                            ack_get_dict.pop(key)
                if tmp_end_flag:
                    break
                # 超时
                if not self.window.check():
                    # 将所有非超时重传置为RT
                    tmp_point = (self.window.begin_point + 1) % (GbnConfig.SW_SIZE + 1)
                    while tmp_point != seq:
                        self.window.set_status(tmp_point, "RT")
                        tmp_point = (tmp_point + 1) % (GbnConfig.SW_SIZE + 1)
                    seq = self.window.begin_point
                if seq == self.window.unused_point:
                    continue
                # 发送数据帧

                # TODO:
                if seq != self.window.file_end_point:
                    # GbnConfig.print(self.window.get_data(seq))
                    self.udp_handle.send(self.window.get_data(seq))
                    GbnLog.send_log(self.udp_handle.send_count, seq,
                                    self.window.get_status(seq), self.window.unused_point)
                    self.window.set_status(seq)
                    self.window.start_timing(seq)
                    seq = (seq + 1) % (GbnConfig.SW_SIZE + 1)
            GbnLog.send_done(self.udp_handle.send_count, self.window.send_count, file_handle.file_path, dst_mac)
            self.window.close_pbar()
            self.udp_handle.clear_send_count()
            GbnConfig.print(f"[INFO] File:{message} Send Finish!")
