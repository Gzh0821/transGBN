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

from GbnTool import logging
from GbnTool.AddrTool import MACAddress


class GbnLog:
    _send_logger = logging.getLogger('SendLogger')
    _receive_logger = logging.getLogger('ReceiveLogger')

    @staticmethod
    def init(send_file: str, receive_file: str, show: bool = True):
        """
        Init the Logging.
        :param send_file: file to storage send log.
        :param receive_file: file to storage receive log.
        :param show: if show the log in terminal.
        :return:
        """
        formatter = logging.Formatter('[%(levelname)s][%(net_type)s]#%(asctime)s#: %(message)s')

        GbnLog._send_logger.setLevel(logging.DEBUG)
        GbnLog._receive_logger.setLevel(logging.DEBUG)

        send_handler = logging.FileHandler(filename=send_file)
        send_handler.setFormatter(formatter)

        receive_handler = logging.FileHandler(filename=receive_file)
        receive_handler.setFormatter(formatter)

        GbnLog._send_logger.addHandler(send_handler)
        GbnLog._receive_logger.addHandler(receive_handler)

        if show:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.DEBUG)

            GbnLog._send_logger.addHandler(stream_handler)
            GbnLog._receive_logger.addHandler(stream_handler)

    @staticmethod
    def send_log(num: int, pdu_to_send: int, status: str, ack_no: int):
        """
        Log the send information.
        :param num:
        :param pdu_to_send:
        :param status:
        :param ack_no:
        :return:
        """
        if status == "New":
            GbnLog._send_logger.info(f"(No:{num})(pdu_to_send:{pdu_to_send})(status:{status})(ackedNo:{ack_no})",
                                     extra={"net_type": "Send"})
        else:
            GbnLog._send_logger.warning(f"(No:{num})(pdu_to_send:{pdu_to_send})(status:{status})(ackedNo:{ack_no})",
                                        extra={"net_type": "Send"})

    @staticmethod
    def send_done(num: int, pdu_count: int, file_name: str, mac_addr: MACAddress):
        """
        Log the reception done information.
        :param num:
        :param pdu_count:
        :param file_name:
        :param mac_addr:
        :return:
        """
        GbnLog._send_logger.info(
            f"(FileName:{file_name})(DstMac:{str(mac_addr)})(TotalNo:{num})(TotalPduCount:{pdu_count})",
            extra={"net_type": "SendDone"})

    @staticmethod
    def receive_log(num: int, pdu_exp: int, pdu_recv: int, status: str = "OK", net_type: str = "Receive", pdu_count=-1):
        """
        Log the reception information.
        :param num:
        :param pdu_exp:
        :param pdu_recv:
        :param status:
        :param net_type:
        :param pdu_count:
        :return:
        """
        if status == "OK":
            GbnLog._receive_logger.info(
                f"(No:{num})(pdu_exp:{pdu_exp})(status:{status})(pdu_recv:{pdu_recv})(pdu_count:{pdu_count})",
                extra={"net_type": net_type})
        else:
            GbnLog._receive_logger.error(f"(No:{num})(pdu_exp:{pdu_exp})(status:{status})(pdu_recv:{pdu_recv})",
                                         extra={"net_type": net_type})

    @staticmethod
    def receive_done(num: int, pdu_count: int, file_name: str, mac_addr: MACAddress):
        """
        Log the reception done information.
        :param num:
        :param pdu_count:
        :param file_name:
        :param mac_addr:
        :return:
        """
        GbnLog._receive_logger.info(
            f"(FileName:{file_name})(SrcMac:{str(mac_addr)})(TotalNo:{num})(TotalPduCount:{pdu_count})",
            extra={"net_type": "ReceiveDone"})
