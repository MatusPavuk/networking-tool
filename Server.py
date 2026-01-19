from scapy.layers.inet import IP, TCP, UDP
from scapy.all import *

import os
import threading
import random
import socket
import time

from utils.TCP_FLAGS import TCPFlags
from utils.PacketAndFilterBuilder import PacketAndFilterBuilder
from utils.SIPPacketLayerBuilder import SIPPacketLayerBuilder


class Server:

    # Constructor. Declaration and initialization of variables.
    # Automatic IP address assignment based on chosen Network Interface
    def __init__(self, stop_generating, print_function, network_interface, is_generating):

        self.stop_generating = stop_generating
        self.print_function = print_function
        self.nic = network_interface
        self.is_generating = is_generating

        # Network variables
        self.port = None
        self.ip_address = get_if_addr(network_interface)
        self.client_port = None
        self.client_ip_address = ""
        self.basic_filter = None
        self.packet_and_filter_builder = None

        # TCP Variables
        self.seq = 300
        self.ack = 0
        self.last_client_ack = None
        self.not_acked_data = {}
        self.packet = None
        self.sent_all = False
        self.variant = ""

        # UDP Variables
        self.timestamp = 0
        self.synchronization = random.randint(0, 2 ** 32 - 1)
        self.stop_by_me = False
        self.sip_layer_builder = None

        # Threading variables
        self.pause_transmission = threading.Event()
        self.send_thread = None


    # Declaration and initialization of sockets for TCP and UDP. Assignment of free TCP and UDP port.
    def _initialize_sockets(self):
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_tcp.bind(('0.0.0.0', 0))
        self.port_tcp = self.socket_tcp.getsockname()[1]

        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_udp.bind(('0.0.0.0', 0))
        self.port_udp = self.socket_udp.getsockname()[1]


    # Method to handle connection request and call method for sniffing and processing based on protocol
    def start_and_handle_connection(self):

        self._initialize_sockets()
        self.print_function(f"[SERVER] started on TCP - {self.ip_address}:{self.port_tcp}\n[SERVER] started on UDP - {self.ip_address}:{self.port_udp}\n")
        self._detect_and_init_protocol()

        # UDP
        if self.variant == "voip":
            self._sniff_packets_voip()
        # TCP
        else:
            self._sniff_and_process_tcp_packets()

    # Method to sniff first packet and determine if traffic will be TCP or UDP and call according methods
    def _detect_and_init_protocol(self):
        self.packet = sniff(iface=self.nic,
                            filter=f"( ( (tcp[tcpflags] & tcp-syn != 0) and (tcp[13] & 0x04 == 0) and dst port {self.port_tcp} ) or (udp and dst port {self.port_udp}) ) and dst host {self.ip_address}",
                            count=1)
        if self.packet:
            self.packet = self.packet[0]

            if self.packet.haslayer(TCP):
                self.port = self.port_tcp
                self.socket_udp.close()
                self._tcp_three_way_handshake()

            elif self.packet.haslayer(UDP):
                self.variant = "voip"
                self.port = self.port_udp
                self.socket_tcp.close()
                self.seq = 0
                self.ack = None
                self._answer_voip_sip_init()


    # -------------------------------------------- TCP -----------------------------------------------------------------
    # Method for handling initiation of communication - three-way handshake
    def _tcp_three_way_handshake(self):

        # Sniff only TCP SYN packets and ignore RST packets (Windows TCP stack problem) - possible new connections from clients
        # SYN
        if self.packet[TCP].flags == TCPFlags.SYN:
            print(f"[SERVER] Received SYN packet from IP - {self.packet[IP].src} - Port: {self.packet[TCP].sport}")
            self.client_ip_address = self.packet[IP].src
            self.client_port = self.packet[TCP].sport
            self.ack = self.packet[TCP].seq + 1
            self.packet_and_filter_builder = PacketAndFilterBuilder(self.client_ip_address, self.client_port, self.ip_address, self.port)
            self.basic_filter = self.packet_and_filter_builder.build_basic_filter("tcp")

            packet_syn_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("SA", self.seq, self.ack)
            time.sleep(0.1)
            send(packet_syn_ack, verbose=False)
            print(f"[SERVER] Sent SYN-ACK packet to IP - {self.client_ip_address} - Port: {self.client_port}")

        # Sniff ACK packet
        self.packet = sniff(iface=self.nic,
                            filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                            count=1)[0]

        if self.packet[TCP].flags == TCPFlags.ACK:  # ACK
            print("[SERVER] Received ACK packet, beginning transmission of data...")
            self.last_client_ack = self.packet[TCP].ack
            self.seq += 1
            self.ack = self.packet[TCP].seq
            self._await_type_of_traffic()
            self.send_thread = threading.Thread(target=self._send_data)
            self.send_thread.start()


    # Method to set type of traffic that server should generate based on received packets with traffic type string
    def _await_type_of_traffic(self):
        self.packet = sniff(iface=self.nic,
                            filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                            count=1)[0]

        if self.packet.haslayer(Raw):
            raw_data = self.packet[Raw].load
            self.variant = raw_data.decode('utf-8')
            print(f"Obtained variant - {self.variant}")

            self.ack = self.packet[TCP].seq + 1

            packet_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack)
            send(packet_ack, verbose=False)


    def _sniff_and_process_tcp_packets(self):

        sniff_filter = self.basic_filter + f" and (tcp[13] & {TCPFlags.RST} == 0)"

        while True:
            self.packet = sniff(iface=self.nic,
                                filter=sniff_filter,
                                count=1, timeout=10)

            if self.packet:
                self.packet = self.packet[0]

                if self.packet.haslayer(TCP):

                    # Received FIN packet
                    if self.packet[TCP].flags == TCPFlags.FIN:
                        self.stop_generating.set()
                        self._teardown_as_responder()
                        break
                    # ACk in order
                    if self.packet[TCP].ack > self.last_client_ack:
                        self._process_client_ack()

                        if self.sent_all and self.stop_generating.is_set():
                            self._teardown_as_initiator()
                            break

                    # Low / duplicate ACK = need for retransmission
                    #else:
                    #    self._retransmit_not_delivered_packets()
            elif self.stop_generating.is_set():
                self._teardown_as_initiator()
                break


    def _process_client_ack(self):
        self.last_client_ack = self.packet[TCP].ack
        if self.pause_transmission.is_set():
            self.pause_transmission.clear()

        for key in list(self.not_acked_data.keys()):
            if key <= self.last_client_ack:
                del self.not_acked_data[key]


    #def _retransmit_not_delivered_packets(self):
    #    for seq in sorted(self.not_acked_data.keys()):
    #        if seq >= self.last_client_ack:
    #            send(self.not_acked_data[seq], verbose=False)


    # Method with main logic for sending packets based on type of traffic chosen / obtained
    def _send_data(self):
        time.sleep(2)

        if self.variant == "video_demand":
            self._tcp_send_video_demand()

        elif self.variant == "video_live":
            self._tcp_send_video_live()

        elif self.variant == "audio_live":
            self._tcp_send_audio_live()

        elif self.variant == "audio_demand":
            self._tcp_send_audio_demand()

        print("[SERVER] Sent all data, beginning four-way end of session.")
        self.sent_all = True


    def _tcp_send_video_demand(self):
        """
            Priemerná dĺžka burstu = 6s
            Dĺžka pauzy medzi burstami = 13s - 17s
            Poslaných paketov v burstoch = 6000 - 9000
        """

        burst_duration = 6
        packets_per_ack = 25
        while not self.stop_generating.is_set():
            start = time.time()
            end = start + burst_duration
            while time.time() <= end:
                packets_to_be_send = [
                    self.packet_and_filter_builder.build_ip_tcp_packet_layers("PA", self.seq + (i * 1412), self.ack) /
                    Raw(RandString(1412)) for i in range(packets_per_ack)
                ]
                self.seq += packets_per_ack * 1412
                send(packets_to_be_send, verbose=False)
            time.sleep(random.randrange(13, 17, 1))


    def _tcp_send_video_live(self):
        while not self.stop_generating.is_set():
            packet_to_be_send = [
                self.packet_and_filter_builder.build_ip_tcp_packet_layers("PA", self.seq, self.ack) /
                Raw(RandString(1440))
            ]
            self.seq += 1440
            send(packet_to_be_send, verbose=False)


    def _tcp_send_audio_demand(self):
        """
            - Spotify - audio on demand (Pre-recorded audio)
            - Burst každých 10 s
            - V jednej sekunde 126 packetov
            - Dĺžka paketu server -> klient = 1452 bytes (payload)
        """

        while not self.stop_generating.is_set():

            for _ in range(9):
                packets_to_be_send = [
                    self.packet_and_filter_builder.build_ip_tcp_packet_layers("PA", self.seq + (j * 1456), self.ack) /
                    Raw(RandString(1456)) for j in range(13)
                ]
                self.seq += 13 * 1456
                send(packets_to_be_send, verbose=False)

            time.sleep(10)


    def _tcp_send_audio_live(self):

        """
        - Striedanie 2 cykly a 3 cykly
        - 2 cykly - 12 paketov
        - 3 cykly - 18 paketov
        - 1 cyklus - 6 Server -> klient a 1 klient -> server
        - dlzka payload-u server -> klient - 1456 bytes
        """
        
        packets_in_cycle = 5
        cycles_in_second = 2
        base_interval = 0.4
        next_time = time.perf_counter()
        while not self.stop_generating.is_set():

            for _ in range(cycles_in_second):
                packets_to_be_send = [
                    self.packet_and_filter_builder.build_ip_tcp_packet_layers("PA", self.seq + (j * 1456), self.ack) /
                    Raw(RandString(1456)) for j in range(packets_in_cycle)
                ]
                self.seq += packets_in_cycle * 1456
                send(packets_to_be_send, verbose=False)

                next_time += base_interval
                sleep_duration = next_time - time.perf_counter()
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
            cycles_in_second = 3 if cycles_in_second == 2 else 2


    # Method to handle end of session and connection
    def _teardown_as_initiator(self):
        packet_fin = self.packet_and_filter_builder.build_ip_tcp_packet_layers("F", self.seq, self.ack)
        send(packet_fin, verbose=False)
        print("[SERVER] Sent FIN packet.")

        while True:
            self.packet = sniff(iface=self.nic,
                                filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                                count=1,
                                timeout=5)
            if self.packet:
                break
            else:
                send(packet_fin, verbose=False)
                print("[SERVER] Sent FIN packet.")

        if self.packet[0][TCP].flags == TCPFlags.FIN_ACK:
            print("[SERVER] Received FIN-ACK, sending ACK and terminating")
            self.seq = self.packet[0][TCP].ack
            self.ack = self.ack + 1
            last_ack_packet = self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack)
            time.sleep(2)
            send(last_ack_packet, verbose=False)
            print("[SERVER] Sent last ACK packet.")
            if self.socket_tcp:
                self.socket_tcp.close()
            self.stop_generating.clear()
            if self.is_generating:
                self.is_generating.set(False)


    def _teardown_as_responder(self):
        print("[SERVER] Received FIN packet, sending FIN-ACK packet")
        # Ak moje posledné poslané ACK menej ako seq vo FIN, ktorý som dostal tak ACK a retransmission ---------- ??????????
        packet_fin_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("FA", self.packet[TCP].ack, self.packet[TCP].seq + 1)
        time.sleep(2)
        send(packet_fin_ack, verbose=False)
        packets = sniff(iface=self.nic,
                        filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                        count=5,
                        timeout=10)
        if packets:
            for packet in packets:
                if packet.haslayer(TCP) and packet[TCP].flags == TCPFlags.ACK:  # packet[TCP].seq == self.seq+1:
                    print("[SERVER] Received ACK, terminating")
                    if self.socket_tcp:
                        self.socket_tcp.close()
                        if self.is_generating:
                            self.is_generating.set(False)


    # --------------------------------------------- VoIP ----------------------------------------------------------------
    # Method to answer SIP INVITE received from client
    def _answer_voip_sip_init(self):

        if self.packet and self.packet.haslayer(UDP):
            self._initialize_voip_variables()


        packet_100 = self.packet_and_filter_builder.build_ip_udp_packet_layers() / \
                     Raw(load=self.sip_layer_builder.build_100_trying())
        send(packet_100, verbose=False)

        packet_180 = self.packet_and_filter_builder.build_ip_udp_packet_layers() / \
                     Raw(load=self.sip_layer_builder.build_180_ringing())
        send(packet_180, verbose=False)

        packet_200 = self.packet_and_filter_builder.build_ip_udp_packet_layers() / \
                     Raw(load=self.sip_layer_builder.build_200_ok("server", "invite"))
        send(packet_200, verbose=False)

        sip_ack = sniff(iface=self.nic,
                        filter=self.basic_filter,
                        count=1)

        if sip_ack and sip_ack[0].haslayer(Raw):
            payload = sip_ack[0][Raw].load.decode('utf-8')
            if payload.startswith("ACK sip:"):
                self.send_thread = threading.Thread(target=self._voip_rtp_transfer)
                self.send_thread.start()


    def _initialize_voip_variables(self):
        self.client_ip_address = self.packet[IP].src
        self.client_port = self.packet[UDP].sport
        self.packet_and_filter_builder = PacketAndFilterBuilder(self.client_ip_address, self.client_port, self.ip_address, self.port)
        self.sip_layer_builder = SIPPacketLayerBuilder(self.ip_address, self.port, self.client_ip_address,
                                                       self.client_port)
        self.basic_filter = self.packet_and_filter_builder.build_basic_filter("udp")


    # Stop filter for VoIP sniff method
    def _stop_sniff_voip(self, pkt):
        if pkt.haslayer(UDP) and pkt.haslayer(Raw):
            payload = pkt[Raw].load.decode("utf-8", errors="ignore")
            if payload.startswith("BYE sip:"):
                self.stop_generating.set()
                return True
        if self.stop_generating.is_set():
            self.stop_by_me = True
            return True
        return False


    # Method to sniff incoming packets in VoIP
    def _sniff_packets_voip(self):
        sniff(iface=self.nic,
              filter=self.basic_filter,
              stop_filter=self._stop_sniff_voip)

        if self.stop_by_me:
            self._voip_termination_as_initiator()
        else:
            self._voip_termination_as_responder()


    # Method for sending voice data in VoIP using RTP protocol
    def _voip_rtp_transfer(self):

        base_interval = 0.02
        next_time = time.perf_counter()

        while not self.stop_generating.is_set():
            rtp_head = (
                    b'\x80\x09' +
                    self.seq.to_bytes(2, byteorder='big') +
                    self.timestamp.to_bytes(4, byteorder='big') +
                    self.synchronization.to_bytes(4, 'big')
            )
            rtp_load = os.urandom(160)

            rtp_packet = (
                    self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                    Raw(load=rtp_head + rtp_load)
            )

            send(rtp_packet, verbose=False)

            self.timestamp += 160
            self.seq += 1

            jitter = random.uniform(-0.008, 0.008)
            interval = base_interval + jitter

            next_time += interval
            sleep_duration = next_time - time.perf_counter()
            if sleep_duration > 0:
                time.sleep(sleep_duration)


    # Method to handle VoIP connection and session termination as initiator
    def _voip_termination_as_initiator(self):
        bye_packet = (self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                      Raw(load=self.sip_layer_builder.build_bye("server")))

        send(bye_packet, verbose=False)

        sip_ok = sniff(iface=self.nic,
                       filter=self.basic_filter,
                       count=1)[0]

        if sip_ok and sip_ok.haslayer(Raw):
            payload_ok = sip_ok[Raw].load.decode('utf-8')
            if payload_ok.startswith("SIP/2.0 200 OK"):
                if self.is_generating:
                    self.is_generating.set(False)


    # Method to handle VoIP connection and session termination as responder
    def _voip_termination_as_responder(self):
        ok_packet = (self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                     Raw(load=self.sip_layer_builder.build_200_ok("server", "bye")))

        send(ok_packet, verbose=False)
        if self.is_generating:
            self.is_generating.set(False)