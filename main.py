import GbnTool.ByteTool
from GbnFrame import *


if __name__ == '__main__':
    print(math.ceil(math.log(255+1, 2) / 8))
    a = b'\xab'
    print(len(a))
    print(GbnTool.ByteTool.to_binary_str(a))
    src_mac = MACAddress.from_str("0F:00:00:00:00:00")
    dst_mac = MACAddress.from_str("FF:00:00:00:01:00")
    data = {"src_mac":  src_mac, "dst_mac": dst_mac, "seq_num": 10, "ack_num": 10,
            "payload": "Hello"}
    p = GBNFrame(**data)
    print(GbnTool.ByteTool.to_binary_str(p.to_bytes()))
    q = GBNFrame.from_bytes(p.to_bytes())
    if p == q:
        print("Yes!")
