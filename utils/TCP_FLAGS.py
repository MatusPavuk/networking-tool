from enum import IntEnum

class TCPFlags(IntEnum):
    FIN = 0x01,
    SYN = 0x02,
    RST = 0x04,
    PSH = 0x08,
    ACK = 0x10,
    FIN_ACK = 0x11,
    SYN_ACK = 0x12