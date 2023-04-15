from GbnTool import crcmod, time
from GbnTool.AddrTool import MACAddress
from GbnTool.ConfigTool import GbnConfig
from GbnTool.ErrorTool import CRCError
from GbnTool.FileTool import FileReader


class GbnFrame:
    START_FLAG = GbnConfig.START_FLAG
    DATA_FRAME = True

    def __init__(self, src_mac: MACAddress, dst_mac: MACAddress, seq_num: int, payload: bytes):
        if src_mac == dst_mac:
            raise ValueError('Source and destination MAC addresses cannot be the same')

        self.src_mac_addr = src_mac  # 源MAC地址
        self.dst_mac_addr = dst_mac  # 目的MAC地址

        self.seq_num = seq_num  # 帧的序列号

        if len(payload) > GbnConfig.DATA_SIZE:
            raise ValueError('Payload is too long')
        self.payload = payload  # 帧的数据

    @property
    def frame_bytes(self):
        """
        Encapsulates the frame into a byte string in binary format.
        :return:
        """
        # 将帧的序列号、确认号、数据封装成二进制格式的字节串
        src_mac = bytes(self.src_mac_addr)
        dst_mac = bytes(self.dst_mac_addr)
        seq_bytes = self.seq_num.to_bytes(GbnConfig.SEQ_BIT_SIZE, byteorder='big')
        payload_bytes = self.payload

        # 计算CRC校验码
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        crc = crc_func(self.START_FLAG + src_mac + dst_mac + seq_bytes + payload_bytes)
        checksum = crc.to_bytes(2, byteorder='big')
        # 将源MAC地址、目的MAC地址、序列号、确认号、数据、校验和合并成一个字节串，并在开头加上起始标志
        return self.START_FLAG + src_mac + dst_mac + seq_bytes + payload_bytes + checksum

    def __bytes__(self):
        return self.frame_bytes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GbnFrame):
            return False
        return self.frame_bytes == other.frame_bytes

    def __hash__(self) -> int:
        return hash(self.frame_bytes)


class AckFrame(GbnFrame):
    START_FLAG = GbnConfig.ACK_FLAG
    DATA_FRAME = False

    def __init__(self, src_mac: MACAddress, dst_mac: MACAddress, ack_num: int):
        super().__init__(src_mac, dst_mac, ack_num, b"")


class FrameFactory:
    @staticmethod
    def from_bytes(frame_bytes: bytes):
        flag = frame_bytes[0]
        # 从二进制格式的字节串中解析出序列号、确认号、数据和CRC校验码
        if flag != int.from_bytes(GbnConfig.START_FLAG, byteorder='big') and flag != int.from_bytes(
                GbnConfig.ACK_FLAG, byteorder='big'):
            raise ValueError('Invalid frame format')
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        computed_crc = crc_func(frame_bytes[0:-2])
        checksum = int.from_bytes(frame_bytes[-2:], byteorder='big')
        if computed_crc != checksum:
            raise CRCError('CRC error', frame_bytes, computed_crc, checksum)
        src_mac = MACAddress.from_bytes(frame_bytes[1:7])
        dst_mac = MACAddress.from_bytes(frame_bytes[7:13])
        seq_num = int.from_bytes(frame_bytes[13:13 + GbnConfig.SEQ_BIT_SIZE], byteorder='big')
        payload = frame_bytes[13 + GbnConfig.SEQ_BIT_SIZE:-2]
        if flag == int.from_bytes(GbnConfig.START_FLAG, byteorder='big'):
            return GbnFrame(src_mac, dst_mac, seq_num, payload)
        else:
            return AckFrame(src_mac, dst_mac, seq_num)


class GbnWindows:
    def __init__(self, dst_mac: MACAddress) -> None:
        self.src_mac = GbnConfig.MAC_ADDRESS
        self.dst_mac = dst_mac
        self.windows_list = [{"time": 0.0, "data": b"", "type": "New"} for _ in range(0, GbnConfig.SW_SIZE + 1)]
        self.unused_point = (GbnConfig.INIT_SEQ_NO + GbnConfig.SW_SIZE) % (GbnConfig.SW_SIZE + 1)
        self.file_handle = None
        self.if_end = False
        self.file_end_point = -1

    def bind_file(self, file_handle: FileReader):
        self.file_handle = file_handle
        seq = GbnConfig.INIT_SEQ_NO
        while seq != self.unused_point:
            payload = next(self.file_handle)
            if payload is not None:
                self.windows_list[seq]["data"] = GbnFrame(self.src_mac, self.dst_mac, seq, payload).frame_bytes
                self.windows_list[seq]["Type"] = "New"
            else:
                self.file_end_point = seq
                self.if_end = True
                break
            seq = (seq + 1) % (GbnConfig.SW_SIZE + 1)

    def slide(self, ack_num: int):
        tmp_point = self.unused_point
        while tmp_point != ack_num and not self.if_end:
            self.windows_list[tmp_point]["time"] = 0.0
            payload = next(self.file_handle)
            if payload is not None:
                self.windows_list[tmp_point]["data"] = GbnFrame(self.src_mac, self.dst_mac, tmp_point,
                                                                payload).frame_bytes
                self.windows_list[tmp_point]["Type"] = "New"
            else:
                self.if_end = True
                self.file_end_point = tmp_point
                self.windows_list[tmp_point]["data"] = b""
                self.windows_list[tmp_point]["Type"] = "None"
                break
            tmp_point = (tmp_point + 1) % (GbnConfig.SW_SIZE + 1)
        self.windows_list[tmp_point]["time"] = 0.0
        self.windows_list[tmp_point]["data"] = b""
        self.unused_point = ack_num

    @property
    def begin_point(self):
        return (self.unused_point + 1) % (GbnConfig.SW_SIZE + 1)

    def start_timing(self, point: int):
        self.windows_list[point]["time"] = time.time()

    def check(self) -> bool:
        stime = self.windows_list[self.begin_point]["time"]
        if stime == 0.0 or (time.time() - stime) * 1000 <= GbnConfig.TIME_OUT:
            return True
        return False

    def get_data(self, point: int):
        return self.windows_list[point]["data"]

    def get_status(self, point: int):
        return self.windows_list[point]["Type"]

    def set_status(self, point: int, status: str = "TO"):
        self.windows_list[point]["Type"] = status

    def __len__(self):
        return GbnConfig.SW_SIZE
