from GbnTool import binascii


# 二进制串相关工具

def to_binary_str(src: bytes) -> str:
    """
    Change bytes to binary str.
    :param src: bytes string
    :return: str
    """
    hex_string = binascii.hexlify(src).decode()

    # 将十六进制字符串转换为二进制字符串
    binary_string = ' '.join(format(int(hex_string[i:i + 2], 16), '08b') for i in range(0, len(hex_string), 2))

    # 输出二进制字符串
    return binary_string
