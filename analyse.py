from datetime import datetime
import os
import configparser
import re
import sys
import matplotlib.pyplot as plt

# 使用须分别将两组程序置于gbn_1目录和gbn_2目录下
# 配置gbn_1的config.ini包含Test项的DestMac和FilePath，配置gbn_2的config.ini不含Test项
# 运行前先手动运行\gbn_2\main.py，然后运行该测试分析程序


class analyse:
    def __init__(self):
        self.sec_dict = {"DataSize": "GbnFrame", "SWSize": "GbnFrame", "InitSeqNo": "GbnFrame", "Timeout": "Trans",
                         "SendLogName": "Log", "ReceiveLogName": "Log", "ErrorRate": "Random", "LostRate": "Random"}
        self.gbn_1_path = os.path.join(".", "gbn_1", "")
        self.gbn_2_path = os.path.join(".", "gbn_2", "")
        self.send_log_1_path = None
        self.send_log_2_path = None
        self.recv_log_1_path = None
        self.recv_log_2_path = None
        self.config_1_path = os.path.join(".", "gbn_1", "config.ini")
        self.config_2_path = os.path.join(".", "gbn_2", "config.ini")
        self.standard_config_path = "standard_config.ini"
        self.anal_data_path = os.path.join(".", "anal", "analysations", "")
        self.anal_conf_path = os.path.join(".", "anal", "configs", "")
        self.anal_fig_path = os.path.join(".", "anal", "figs", "")

        self.test_times = 1
        self.datasize = 0
        self.swsize = 0
        self.timeout = 0
        self.send_log_name = ""
        self.recv_log_name = ""
        self.errorrate = 0
        self.lostrate = 0
        self.start_time = 0.0
        self.end_time = 0.0
        self.num_count = 0
        self.pdu_count = 0
        self.timeout_count = 0
        self.retrans_count = 0
        self.change_value_list = []
        self.time_cost_list = []
        self.num_count_list = []
        self.pdu_count_list = []
        self.TO_count_list = []
        self.total_RT_count_list = []

    def read_config(self):
        conf = configparser.ConfigParser()
        conf.read(self.standard_config_path)
        # 读取标准配置文件
        if not conf.has_section("GbnFrame"):
            raise ValueError("GbnFrame config not found in config.ini")
        self.datasize = conf.getint("GbnFrame", "DataSize")
        self.swsize = conf.getint("GbnFrame", "SWSize")
        if not conf.has_section("Trans"):
            raise ValueError("Trans config not found in config.ini")
        self.timeout = conf.getint("Trans", "Timeout")
        if not conf.has_section("Log"):
            raise ValueError("Log config not found in config.ini")
        self.send_log_name = conf.get("Log", "SendLogName")
        self.recv_log_name = conf.get("Log", "ReceiveLogName")
        self.send_log_1_path = os.path.join(".", "gbn_1", self.send_log_name)
        self.send_log_2_path = os.path.join(".", "gbn_2", self.send_log_name)
        self.recv_log_1_path = os.path.join(".", "gbn_1", self.recv_log_name)
        self.recv_log_2_path = os.path.join(".", "gbn_2", self.recv_log_name)
        if not conf.has_section("Random"):
            raise ValueError("Random config not found in config.ini")
        self.errorrate = conf.getint("Random", "ErrorRate")
        self.lostrate = conf.getint("Random", "LostRate")
        print(
            f"Config: DataSize={self.datasize}, SWSize={self.swsize}, Timeout={self.timeout}, ErrorRate={self.errorrate}, LostRate={self.lostrate}")

    def change_config(self, sec: str, opt: str, para: str):
        conf1 = configparser.ConfigParser()
        conf2 = configparser.ConfigParser()
        # 设置不改变配置项名大小写
        conf1.optionxform = lambda option: option
        conf2.optionxform = lambda option: option
        conf1.read(self.config_1_path)
        conf2.read(self.config_2_path)
        # 修改配置项
        conf1.set(sec, opt, para)
        conf2.set(sec, opt, para)
        with open(self.config_1_path, 'w') as confw:
            conf1.write(confw)
        with open(self.config_2_path, 'w') as confw:
            conf2.write(confw)

    def update(self, type: str, value: int):
        setattr(self, type.lower(), value)

    def read_send_log(self, num: int, cnt: int):
        with open(self.send_log_1_path, 'r') as send_log:
            for line in send_log:
                self.status = re.search(
                    r'(?<=(\]\[)).*(?=(\]#))', line).group()
                # 匹配Send和Warning记录
                if(self.status != "SendDone"):
                    self.time = datetime.strptime(re.search(
                        r'(?<=(#)).*(?=(#))', line).group(), '%Y-%m-%d %H:%M:%S,%f').timestamp()
                    self.num = int(re.search(r'(?<=(No:))\d+', line).group())
                    self.type = re.search(
                        r'(?<=(status:)).{2,3}(?=(\)\())', line).group()
                    if(self.num == 1):
                        self.start_time = self.time
                    if(self.type == "TO"):
                        self.timeout_count += 1
                        self.retrans_count += 1
                    elif(self.type == "RT"):
                        self.retrans_count += 1
                # 匹配SendDone记录
                else:
                    self.end_time = datetime.strptime(re.search(
                        r'(?<=(#)).*(?=(#))', line).group(), '%Y-%m-%d %H:%M:%S,%f').timestamp()
                    self.num_count = int(
                        re.search(r'(?<=(TotalNo:))\d+', line).group())
                    self.pdu_count = int(
                        re.search(r'(?<=(TotalPduCount:))\d+', line).group())
        if cnt == 0:
            # 向绘图用列表中添加项
            self.time_cost_list.append(
                (self.end_time - self.start_time) / self.test_times)
            self.num_count_list.append(self.num_count / self.test_times)
            self.pdu_count_list.append(self.pdu_count)
            self.TO_count_list.append(self.timeout_count / self.test_times)
            self.total_RT_count_list.append(
                self.retrans_count / self.test_times)
        else:
            # 将值加到已有项，实现多次测试取平均值
            self.time_cost_list[num] += (self.end_time - self.start_time) / self.test_times
            self.num_count_list[num] += self.num_count / self.test_times
            self.TO_count_list[num] += self.timeout_count / self.test_times
            self.total_RT_count_list[num] += self.retrans_count / self.test_times

    def remove_log(self):
        # 删除发送方日志
        os.remove(self.recv_log_1_path)
        os.remove(self.send_log_1_path)

    def write(self, handle):
        # 写入分析记录
        data_str = f"[Data](DataSize={self.datasize})(SWSize={self.swsize})\
(Timeout={self.timeout})(ErrorRate={self.errorrate})(LostRate={self.lostrate})\
(TimeCost={self.end_time - self.start_time})(NumCount={self.num_count})\
(PDUCount={self.pdu_count})(TOCount={self.timeout_count})(TotalRTCount={self.retrans_count})\n"
        handle.write(data_str)

    def reset_value(self):
        self.start_time = 0.0
        self.end_time = 0.0
        self.num_count = 0
        self.pdu_count = 0
        self.timeout_count = 0
        self.retrans_count = 0

    def fig_plot(self, status_change: str, conf_id: int):
        # 绘制No/PDU/TO/RT四合一图
        fig1, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(self.change_value_list, self.num_count_list,
                 color='red', linestyle='-', marker='o', label='TotalNo')
        ax1.plot(self.change_value_list, self.pdu_count_list,
                 color='blue', linestyle='--', marker='s', label='TotalPDU')
        ax2.plot(self.change_value_list, self.TO_count_list,
                 color='green', linestyle='-', marker='o', label='TotalTO')
        ax2.plot(self.change_value_list, self.total_RT_count_list,
                 color='gray', linestyle='--', marker='s', label='TotalRT')
        ax1.set_xlabel(f"{status_change}")
        ax1.set_ylabel("No/PDU")
        ax2.set_ylabel("TO/RT")
        ax1.legend(loc='upper center')
        ax2.legend(loc='upper right')
        fig1.savefig(os.path.join(self.anal_fig_path, f"count_chart_{conf_id}.png"), format='png', dpi=300)
        plt.clf()
        # 绘制TimeCost图
        plt.plot(self.change_value_list, self.time_cost_list,
                 color='blue', linestyle='-', marker='o', label='TimeCost')
        plt.xlabel(f"{status_change}")
        plt.ylabel("TimeCost")
        plt.legend(loc='best')
        plt.savefig(os.path.join(self.anal_fig_path, f"time_cost_chart_{conf_id}.png"), format='png', dpi=300)
        plt.clf()

    def reset(self):
        self.change_value_list.clear()
        # 清空绘图列表
        self.time_cost_list.clear()
        self.num_count_list.clear()
        self.pdu_count_list.clear()
        self.TO_count_list.clear()
        self.total_RT_count_list.clear()
        # 重置配置项为标准值
        reset_list = ["DataSize", "SWSize", "InitSeqNo", "Timeout", "SendLogName", "ReceiveLogName", "ErrorRate", "LostRate"]
        conf1 = configparser.ConfigParser()
        conf2 = configparser.ConfigParser()
        standard = configparser.ConfigParser()
        # 设置不改变配置项名大小写
        conf1.optionxform = lambda option: option
        conf2.optionxform = lambda option: option
        conf1.read(self.config_1_path)
        conf2.read(self.config_2_path)
        standard.read(self.standard_config_path)
        # 修改配置项
        for status in reset_list:
            para = standard.get(self.sec_dict[status], status)
            conf1.set(self.sec_dict[status], status, para)
            conf2.set(self.sec_dict[status], status, para)
        with open(self.config_1_path, 'w') as confw:
            conf1.write(confw)
        with open(self.config_2_path, 'w') as confw:
            conf2.write(confw)

    def run(self):
        self.read_config()
        conf_count = int(input("Please input the number of configuration files:"))
        # 循环测试所有配置文件
        for conf_id in range(1,conf_count + 1):
            # 输入待测配置项
            config = configparser.ConfigParser()
            if len(config.read(os.path.join(self.anal_conf_path, f"anal_{conf_id}.ini"))) == 0:
                raise ValueError("Anal config not found")
            status_change = config.get("Anal", "TestStatus")
            if status_change in self.sec_dict:
                sec_change = self.sec_dict[status_change]
            else:
                raise ValueError("Illegal test tag")
            # 输入配置项取值列表
            value_change = config.get("Anal", "Data").split()
            # 输入每数据测试次数
            self.test_times = config.getint("Anal", "Times")

            self.reset()
            data = open(os.path.join(self.anal_data_path, f"analyse_{conf_id}.txt"), 'w')
            # 循环测试分析
            num = 0
            for value in value_change:
                print(f"[ANAL] {status_change}={value}")
                self.change_value_list.append(int(value))
                for cnt in range(0, self.test_times):
                    self.change_config(sec_change, status_change, value)
                    self.update(status_change, int(value))
                    os.chdir(self.gbn_1_path)
                    os.system(sys.executable + " main.py")
                    os.chdir("..")
                    self.read_send_log(num, cnt)
                    self.write(data)
                    self.remove_log()
                    self.reset_value()
                num += 1
            print(f"[ANAL] Test {conf_id} finish!")
            data.close()
            self.fig_plot(status_change, conf_id)
        print(f"[ANAL] Analyse finish!")
        return 0


anal_loop = analyse()
anal_loop.run()
