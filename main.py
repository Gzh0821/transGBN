# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import GbnTool.ByteTool
from GbnFrame import *

# 按间距中的绿色按钮以运行脚本。
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

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
