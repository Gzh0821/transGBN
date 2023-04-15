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

from GbnTool import binascii, re


class MACAddress:
    def __init__(self, mac_str: str, mac_bytes: bytes):
        self.mac_str = mac_str
        self.mac_bytes = mac_bytes

    @classmethod
    def from_str(cls, mac_str: str):
        """
        Create MACAddress object with MAC address with Hex format,like"00:00:00:00:00:00".
        :param mac_str: MAC address with Hex Format
        :return:
        """
        pattern = re.compile('^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
        if pattern.match(mac_str):
            return cls(mac_str, binascii.unhexlify(mac_str.replace(':', '')))
        else:
            raise ValueError('Invalid MAC string address')

    @classmethod
    def from_bytes(cls, mac_bytes: bytes):
        """
        Create MACAddress object with MAC address with Bytes format.
        :param mac_bytes: MAC address with bytes Format
        :return:
        """
        # if len(mac_bytes) != 6:
        #     raise ValueError('Invalid MAC bytes address')
        mac_address_str = binascii.hexlify(mac_bytes).decode('utf-8')
        return cls(':'.join(mac_address_str[i:i + 2] for i in range(0, 12, 2)), mac_bytes)

    def to_bytes(self):
        return self.mac_bytes

    def __bytes__(self):
        return self.mac_bytes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MACAddress):
            return False
        return self.mac_bytes == other.mac_bytes

    def __str__(self) -> str:
        return self.mac_str

    def __hash__(self) -> int:
        return hash(self.mac_bytes)
