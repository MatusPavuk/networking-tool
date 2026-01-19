from scapy.layers.inet import IP, TCP, UDP
from utils.TCP_FLAGS import TCPFlags

class PacketAndFilterBuilder:

    def __init__(self, src_ip, src_port, dst_ip, dst_port):
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port


    def build_ip_tcp_packet_layers(self, packet_flags, packet_seq, packet_ack):
        return (
                IP(dst=self.src_ip, src=self.dst_ip) /
                TCP(dport=self.src_port, sport=self.dst_port, flags=packet_flags,
                    seq=packet_seq,
                    ack=packet_ack)
        )


    def build_ip_udp_packet_layers(self):
        return (
                IP(src=self.dst_ip, dst=self.src_ip) /
                UDP(sport=self.dst_port, dport=self.src_port)
        )


    def build_basic_filter(self, transport_protocol):
        basic_filter = f"{transport_protocol} and src host {self.src_ip} and dst host {self.dst_ip} and src port {self.src_port} and dst port {self.dst_port}"
        if transport_protocol == "tcp":
            return basic_filter + f" and (tcp[13] & {TCPFlags.RST} == 0)"
        else:
            return basic_filter