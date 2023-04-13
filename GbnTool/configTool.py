from GbnTool import configparser, math, random
from GbnTool.AddrTool import MACAddress


# 全局配置工具

def generate_random_mac_address():
    """
    生成随机MAC地址
    """
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return MACAddress.from_str(':'.join(map(lambda x: "%02x" % x, mac)))


class GbnConfig:
    FILE_NAME_FLAG = b'\x81'
    FILE_DATA_FLAG = b'\x99'
    FILE_END_FLAG = b'\xbd'
    DATA_SIZE = SW_SIZE = SEQ_BIT_SIZE = INIT_SEQ_NO = None
    START_FLAG = b'\xab'  # 帧的起始标志
    MAC_ADDRESS: MACAddress = None

    @staticmethod
    def init(config_path: str = "config.ini"):
        _gbn_config = configparser.ConfigParser()
        print("[INFO] GbnConfig reading config.ini...")
        _gbn_config.read(config_path)
        if not _gbn_config.has_section("GbnFrame"):
            raise ValueError("GbnConfig config not found in config.ini")

        # 数据字段的长度
        GbnConfig.DATA_SIZE = _gbn_config.getint("GbnFrame", "DataSize")
        if GbnConfig.DATA_SIZE not in range(1, 4097):
            raise ValueError("DataSize must in (1,4097)")

        # 发送窗口大小
        GbnConfig.SW_SIZE = _gbn_config.getint("GbnFrame", "SWSize")
        if GbnConfig.SW_SIZE < 1:
            raise ValueError("SWSize must be greater than 0")

        # 帧中序列号的位数
        GbnConfig.SEQ_BIT_SIZE = math.ceil(math.log(GbnConfig.SW_SIZE + 1, 2) / 8)

        # 起始PDU编号
        GbnConfig.INIT_SEQ_NO = _gbn_config.getint("GbnFrame", "InitSeqNo")
        if GbnConfig.INIT_SEQ_NO not in range(0, 255):
            raise ValueError("InitSeqNo must in (1,255)")
        print("[INFO] GbnConfig finish config.ini...")

        # 生成随机MAC地址
        GbnConfig.MAC_ADDRESS = MACAddress.from_str(_gbn_config.get("Trans", "LocalMac"))
        print(f"[INFO] Your MAC Address:{GbnConfig.MAC_ADDRESS.mac_str}")
