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

from GbnTool import random


class GbnRandom:
    error_rate = 0
    lost_rate = 0

    @staticmethod
    def init(error_rate: int, lost_rate: int):
        """
        Initial Random Engine.
        :param error_rate: error_rate num (1/n)
        :param lost_rate: lost_rate num (1/n)
        :return:
        """
        GbnRandom.error_rate = 1.0 / error_rate
        GbnRandom.lost_rate = 1.0 / lost_rate

    @staticmethod
    def random_error(data: bytes) -> bytes:
        """
        Randomly modify a bit in the data.
        :param data:
        :return:
        """
        if random.random() < GbnRandom.error_rate:
            byte_array = bytearray(data)
            index = random.randint(0, len(byte_array) - 1)
            byte_as_binary_list = list(bin(byte_array[index])[2:].zfill(8))
            bit_to_modify = random.choice([0, 1])
            byte_as_binary_list[random.randint(0, 7)] = str(bit_to_modify ^ 1)
            byte_array[index] = int(''.join(byte_as_binary_list), 2)
            return bytes(byte_array)
        return data

    @staticmethod
    def keep() -> bool:
        """
        Randomly determine throw the data.
        :return:
        """
        if random.random() < GbnRandom.lost_rate:
            return False
        return True
