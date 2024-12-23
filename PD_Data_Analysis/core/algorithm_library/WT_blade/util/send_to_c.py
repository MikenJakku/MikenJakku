import ctypes
import socket
import numpy as np


class RequestData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("alarm_type", ctypes.c_char * 10),
        ("alarm_desc", ctypes.c_char * 20),
        ("alarm_data", ctypes.c_float * 300),
    ]

    def from_data(self, alarm_type: str, alarm_desc: str, alarm_data: np.ndarray) -> None:
        self.alarm_type = alarm_type.encode()
        self.alarm_desc = alarm_desc.encode()
        for idx, data in enumerate(alarm_data):
            self.alarm_data[idx] = data
        return


class Sender(object):
    def __init__(self) -> None:
        self.socket_fd = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.data = RequestData()
        return

    def send(self, alarm_type: str, alarm_desc: str, alarm_data: np.ndarray) -> None:
        self.data.from_data(alarm_type, alarm_desc, alarm_data)
        send_data = ctypes.string_at(ctypes.addressof(self.data), ctypes.sizeof(self.data))
        self.socket_fd.sendto(send_data, "/tmp/uds_socket")
        return


"""
@code
    calcator = Calcator()
    
    while ValidatingData:
        data = sql.get_data()
        
        alarm_type, alarm_desc, alarm_data = calcator(data)

        try:        
            Sender().send(alarm_type, alarm_desc, alarm_data)
        except Exception as error:
            print(error)
@endcode
"""
