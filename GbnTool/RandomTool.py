from GbnTool import random


class GbnRandom:
    error_rate = 0
    lost_rate = 0

    @staticmethod
    def init(error_rate: int, lost_rate: int):
        GbnRandom.error_rate = 1.0 / error_rate
        GbnRandom.lost_rate = 1.0 / lost_rate

    @staticmethod
    def random_error(data: bytes) -> bytes:
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
        if random.random() < GbnRandom.lost_rate:
            return False
        return True
