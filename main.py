from GbnTool import ByteTool
from GbnTool.FileTool import *
from GbnTool.AddrTool import MACAddress
from GbnTool.UdpTool import *

if __name__ == '__main__':

    src_mac = MACAddress.from_str("0F:00:00:00:00:00")
    dst_mac = MACAddress.from_str("FF:00:00:00:01:00")

    data = {"src_mac": src_mac, "dst_mac": dst_mac, "seq_num": 10, "ack_num": 10,
            "payload": "Hello"}
    upd_handle = UDPCommunication(8888)
    p = SendThread(upd_handle)
    p.run()
    # f = FileWriter()
    # for i in FileReader("temp\\test.pdf"):
    #     data["payload"] = i
    #     p = GbnFrame(**data)
    #     print(ByteTool.to_binary_str(p.frame_bytes))
    #     q = GbnFrame.from_bytes(p.frame_bytes)
    #     if p == q:
    #         print("Yes!")
    #     f.write(q.payload)