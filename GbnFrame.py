import configparser
import math
import crcmod

from GbnTool.AddrTool import *

_gbn_config = configparser.ConfigParser()
_gbn_config.read("config.ini")
if not _gbn_config.has_section("GbnFrame"):
    raise ValueError("GbnFrame config not found")

# 数据字段的长度
DATA_SIZE = _gbn_config.getint("GbnFrame", "DataSize")
if DATA_SIZE not in range(1, 4097):
    raise ValueError("DataSize must in (1,4097)")

# 发送窗口大小
SW_SIZE = _gbn_config.getint("GbnFrame", "SWSize")
if SW_SIZE < 1:
    raise ValueError("SWSize must be greater than 0")

# 帧中序列号的位数
SEQ_BIT_SIZE = math.ceil(math.log(SW_SIZE + 1, 2) / 8)

# 起始PDU编号
INIT_SEQ_NO = _gbn_config.getint("GbnFrame", "InitSeqNo")
if INIT_SEQ_NO not in range(0, 255):
    raise ValueError("InitSeqNo must in (1,255)")


class GBNFrame:
    START_FLAG = b'\xab'  # 帧的起始标志

    def __init__(self, src_mac: MACAddress, dst_mac: MACAddress, seq_num: int, ack_num: int, payload: str):
        if src_mac == dst_mac:
            raise ValueError('Source and destination MAC addresses cannot be the same')

        self.src_mac_addr = src_mac  # 源MAC地址
        self.dst_mac_addr = dst_mac  # 目的MAC地址

        self.seq_num = seq_num  # 帧的序列号
        self.ack_num = ack_num  # 确认号

        if len(payload) > DATA_SIZE:
            raise ValueError('Payload is too long')
        self.payload = payload  # 帧的数据

    def to_bytes(self):
        # 将帧的序列号、确认号、数据封装成二进制格式的字节串
        src_mac = bytes(self.src_mac_addr)
        dst_mac = bytes(self.dst_mac_addr)
        seq_bytes = self.seq_num.to_bytes(SEQ_BIT_SIZE, byteorder='big')
        ack_bytes = self.ack_num.to_bytes(SEQ_BIT_SIZE, byteorder='big')
        payload_bytes = self.payload.encode()
        # 计算CRC校验码
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        crc = crc_func(src_mac + dst_mac + seq_bytes + ack_bytes + payload_bytes)
        checksum = crc.to_bytes(2, byteorder='big')
        # 将源MAC地址、目的MAC地址、序列号、确认号、数据、校验和合并成一个字节串，并在开头加上起始标志
        return self.START_FLAG + src_mac + dst_mac + seq_bytes + ack_bytes + payload_bytes + checksum

    @classmethod
    def from_bytes(cls, frame_bytes):
        # 从二进制格式的字节串中解析出序列号、确认号、数据和CRC校验码
        if frame_bytes[0:1] != cls.START_FLAG:
            raise ValueError('Invalid frame format')
        src_mac = MACAddress.from_bytes(frame_bytes[1:7])
        dst_mac = MACAddress.from_bytes(frame_bytes[7:13])
        seq_num = int.from_bytes(frame_bytes[13:13 + SEQ_BIT_SIZE], byteorder='big')
        ack_num = int.from_bytes(frame_bytes[13 + SEQ_BIT_SIZE:13 + 2 * SEQ_BIT_SIZE], byteorder='big')
        payload = frame_bytes[13 + 2 * SEQ_BIT_SIZE:-2].decode()
        checksum = int.from_bytes(frame_bytes[-2:], byteorder='big')
        # 验证CRC校验码
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        computed_crc = crc_func(frame_bytes[1:-2])
        if computed_crc != checksum:
            raise ValueError('CRC error')
        # 返回一个GBNFrame对象
        return cls(src_mac, dst_mac, seq_num, ack_num, payload)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GBNFrame):
            return False
        return self.__dict__ == other.__dict__
