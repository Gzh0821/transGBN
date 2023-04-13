from GbnTool import crcmod
from GbnTool.AddrTool import MACAddress
from GbnTool.ErrorTool import CRCError
from GbnTool.configTool import GbnConfig


class GbnFrame:

    def __init__(self, src_mac: MACAddress, dst_mac: MACAddress, seq_num: int, ack_num: int, payload: bytes):
        if src_mac == dst_mac:
            raise ValueError('Source and destination MAC addresses cannot be the same')

        self.src_mac_addr = src_mac  # 源MAC地址
        self.dst_mac_addr = dst_mac  # 目的MAC地址

        self.seq_num = seq_num  # 帧的序列号
        self.ack_num = ack_num  # 确认号

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
        ack_bytes = self.ack_num.to_bytes(GbnConfig.SEQ_BIT_SIZE, byteorder='big')
        payload_bytes = self.payload
        # 计算CRC校验码
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        crc = crc_func(src_mac + dst_mac + seq_bytes + ack_bytes + payload_bytes)
        checksum = crc.to_bytes(2, byteorder='big')
        # 将源MAC地址、目的MAC地址、序列号、确认号、数据、校验和合并成一个字节串，并在开头加上起始标志
        return GbnConfig.START_FLAG + src_mac + dst_mac + seq_bytes + ack_bytes + payload_bytes + checksum

    def __bytes__(self):
        return self.frame_bytes

    @classmethod
    def from_bytes(cls, frame_bytes):
        # 从二进制格式的字节串中解析出序列号、确认号、数据和CRC校验码
        if frame_bytes[0:1] != GbnConfig.START_FLAG:
            raise ValueError('Invalid frame format')
        crc_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        computed_crc = crc_func(frame_bytes[1:-2])
        checksum = int.from_bytes(frame_bytes[-2:], byteorder='big')
        if computed_crc != checksum:
            raise CRCError('CRC error', frame_bytes, computed_crc, checksum)
        src_mac = MACAddress.from_bytes(frame_bytes[1:7])
        dst_mac = MACAddress.from_bytes(frame_bytes[7:13])
        seq_num = int.from_bytes(frame_bytes[13:13 + GbnConfig.SEQ_BIT_SIZE], byteorder='big')
        ack_num = int.from_bytes(frame_bytes[13 + GbnConfig.SEQ_BIT_SIZE:13 + 2 * GbnConfig.SEQ_BIT_SIZE],
                                 byteorder='big')
        payload = frame_bytes[13 + 2 * GbnConfig.SEQ_BIT_SIZE:-2]
        return cls(src_mac, dst_mac, seq_num, ack_num, payload)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GbnFrame):
            return False
        return self.frame_bytes == other.frame_bytes

    def __hash__(self) -> int:
        return hash(self.frame_bytes)
