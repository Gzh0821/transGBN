from GbnTool.UdpTool import *
from GbnTool import ByteTool

if __name__ == '__main__':
    port = 12908
    dst_port = 10908
    udp_handle = UDPCommunication(port)
    udp_handle.set_dest("localhost", dst_port)
    p = SendThread(udp_handle)
    p.run()
    # p = SendThread(upd_handle)
    # p.run()
    # f = FileWriter()
    # for i in FileReader("temp\\test.pdf"):
    #     data["payload"] = i
    #     p = GbnFrame(**data)
    #     print(ByteTool.to_binary_str(p.frame_bytes))
    #     q = GbnFrame.from_bytes(p.frame_bytes)
    #     if p == q:
    #         print("Yes!")
    #     f.write(q.payload)
