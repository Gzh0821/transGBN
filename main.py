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

from GbnTool.UdpTool import *

if __name__ == '__main__':
    # 设置本地端口
    udp_handle = UDPCommunication(GbnConfig.UDP_PORT)
    # 设置目标的 IP 和端口
    udp_handle.set_dest(GbnConfig.DEST_IP, GbnConfig.DEST_PORT)
    # 创建发送进程
    p = SendThread(udp_handle)
    # 启动
    p.run()
