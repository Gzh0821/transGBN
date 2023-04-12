import GbnTool.ByteTool
from GbnFrame import *
from GbnTool.FileTool import *

if __name__ == '__main__':
    GbnConfig.init()
    print(math.ceil(math.log(255 + 1, 2) / 8))
    a = b'\xab'
    print(len(a))
    print(GbnTool.ByteTool.to_binary_str(a))
    src_mac = MACAddress.from_str("0F:00:00:00:00:00")
    dst_mac = MACAddress.from_str("FF:00:00:00:01:00")

    data = {"src_mac": src_mac, "dst_mac": dst_mac, "seq_num": 10, "ack_num": 10,
            "payload": "Hello"}
    f = open('new.docx', 'wb')
    for i in FileReader("test.docx"):
        data["payload"] = i
        p = GbnFrame(**data)
        print(GbnTool.ByteTool.to_binary_str(p.frame_bytes))
        q = GbnFrame.from_bytes(p.frame_bytes)
        print(q.__dict__)
        if p == q:
            print("Yes!")
            f.write(q.payload)
    f.close()
