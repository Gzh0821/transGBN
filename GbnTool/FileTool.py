from GbnTool import os, configTool


class FileReader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file = open(file_path, 'rb')
        self.file_size = os.path.getsize(file_path)
        self.read_size = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.read_size >= self.file_size:
            self.file.close()
            raise StopIteration
        else:
            data = self.file.read(configTool.GbnConfig.DATA_SIZE)
            self.read_size += len(data)
            return data

    def __del__(self):
        self.file.close()
