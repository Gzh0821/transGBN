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
