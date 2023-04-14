from GbnTool.UdpTool import *

if __name__ == '__main__':
    udp_handle = UDPCommunication(GbnConfig.UDP_PORT)
    udp_handle.set_dest(GbnConfig.DEST_IP, GbnConfig.DEST_PORT)
    p = SendThread(udp_handle)
    p.run()
