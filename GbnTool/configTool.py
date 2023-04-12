from GbnTool import configparser, math


class GbnConfig:
    DATA_SIZE = SW_SIZE = SEQ_BIT_SIZE = INIT_SEQ_NO = None
    START_FLAG = b'\xab'  # 帧的起始标志

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
