from GbnTool import os, math
from GbnTool.ConfigTool import GbnConfig


# 文件读写工具

class FileReader:
    BUF_SIZE = GbnConfig.DATA_SIZE - 1

    def __init__(self, file_path: str):
        self.end_flag = False
        self.name_point = 0
        self.file_path = file_path
        self.file = open(file_path, 'rb')
        self.file_size = os.path.getsize(file_path)
        binary_data = os.path.basename(file_path).encode()
        self.file_path_list = [(GbnConfig.FILE_NAME_FLAG + binary_data[i:i + self.BUF_SIZE]) for i in
                               range(0, len(binary_data), self.BUF_SIZE)]
        self.read_size = 0

    def __iter__(self):
        return self

    def __next__(self) -> bytes | None:
        if self.name_point < len(self.file_path_list):
            # 返回文件名
            self.name_point += 1
            return self.file_path_list[self.name_point - 1]
        elif self.end_flag:
            # 终止迭代
            return None
        elif self.read_size >= self.file_size:
            # 返回结束标志
            self.file.close()
            self.end_flag = True
            return GbnConfig.FILE_END_FLAG
        else:
            data = self.file.read(GbnConfig.DATA_SIZE - 1)
            self.read_size += len(data)
            # TODO:
            print(data)
            return GbnConfig.FILE_DATA_FLAG + data

    def __del__(self):
        self.file.close()

    def __len__(self):
        return len(self.file_path_list) + math.ceil(self.file_size / (GbnConfig.DATA_SIZE - 1)) + 1


class FileWriter:
    def __init__(self):
        self.file_path = None
        self.file_path_list = []
        self.file = None
        self.if_open = False
        self.count = 0

    def write(self, data: bytes):
        self.count += 1
        if data[0] == int.from_bytes(GbnConfig.FILE_NAME_FLAG, "big"):
            self.file_path_list.append(data[1:].decode())
        if (not self.if_open) and data[0] != int.from_bytes(GbnConfig.FILE_NAME_FLAG, "big"):
            self.if_open = True
            self.file_path = ''.join(self.file_path_list)
            self.file = open(self.file_path, "wb")
            self.file.write(data[1:])
        elif data[0] == int.from_bytes(GbnConfig.FILE_DATA_FLAG, "big"):
            self.file.write(data[1:])
        elif data[0] == int.from_bytes(GbnConfig.FILE_END_FLAG, "big"):
            self.file.close()
            tmp_count = self.count
            tmp_path = self.file_path
            self.reset()
            return tmp_count,tmp_path
        elif data[0] == int.from_bytes(GbnConfig.FILE_NONE_FLAG, "big"):
            return -1,None
        return self.count,None

    def reset(self):
        self.file_path = None
        self.file_path_list = []
        self.file = None
        self.if_open = False
        self.count = 0

    def __del__(self):
        if self.file is not None:
            self.file.close()
