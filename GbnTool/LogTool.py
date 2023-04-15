from GbnTool import logging
from GbnTool.AddrTool import MACAddress

class GbnLog:
    _send_logger = logging.getLogger('SendLogger')
    _receive_logger = logging.getLogger('ReceiveLogger')

    @staticmethod
    def init(send_file: str, receive_file: str, show: bool = True):
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
        if status == "New":
            GbnLog._send_logger.info(f"(No:{num})(pdu_to_send:{pdu_to_send})(status:{status})(ackedNo:{ack_no})",
                                     extra={"net_type": "Send"})
        else:
            GbnLog._send_logger.warning(f"(No:{num})(pdu_to_send:{pdu_to_send})(status:{status})(ackedNo:{ack_no})",
                                        extra={"net_type": "Send"})

    @staticmethod
    def receive_log(num: int, pdu_exp: int, pdu_recv: int, status: str = "OK", net_type: str = "Receive",pdu_count = -1):
        if status == "OK":
            GbnLog._receive_logger.info(f"(No:{num})(pdu_exp:{pdu_exp})(status:{status})(pdu_recv:{pdu_recv})(pdu_count:{pdu_count})",
                                        extra={"net_type": net_type})
        else:
            GbnLog._receive_logger.error(f"(No:{num})(pdu_exp:{pdu_exp})(status:{status})(pdu_recv:{pdu_recv})",
                                         extra={"net_type": net_type})
    def receive_done(num:int,pdu_count:int,file_name:str,mac_addr:MACAddress):
        GbnLog._receive_logger.info(f"(FileName:{file_name})(SrcMac:{str(mac_addr)})(TotalNo:{num})(TotalPduCount:{pdu_count})",
                                        extra={"net_type": "ReceiveDone"})
