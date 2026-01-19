from scapy.layers.inet import IP, TCP, UDP
from scapy.all import *
from collections import deque

import os
import threading
import random
import socket
import time

from utils.TCP_FLAGS import TCPFlags
from utils.PacketAndFilterBuilder import PacketAndFilterBuilder
from utils.SIPPacketLayerBuilder import SIPPacketLayerBuilder

class Client:

    # Constructor. Variables initialization.
    # Automatic assignment of IP address based on chosen NIC.
    # Automatic choice of free port number using socket.
    def __init__(self, variant, server_ip_address, server_port, nic, stop_generating, is_generating):
        # UDP - VoIP related and required variables and operations
        self.variant = variant
        self.is_generating = is_generating
        if variant == "voip":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.stop_by_me = False
            self.timestamp = 0
            self.synchronization = random.randint(0, 2 ** 32 - 1)

        # TCP related and required variables and operations
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.packet_buffer = deque()
            self.packet_buffer_lock = threading.Lock()
            self.ack = 0
            self.processed = 0
            self._initialize_processed_count()

        # Variables used in both TCP and UDP
        self.socket.bind(('0.0.0.0', 0))
        self.port = self.socket.getsockname()[1]
        self.ip_address = get_if_addr(nic)
        self.server_ip = server_ip_address
        self.server_port = server_port
        self.nic = nic
        self.stop_generating = stop_generating
        self.seq = 100
        self.sniff_packets_thread = None
        self.basic_filter = None
        self.packet_and_filter_builder = PacketAndFilterBuilder(self.server_ip, self.server_port, self.ip_address, self.port)

        # SIP layer builder for VoIP
        self.sip_packet_layer_builder = SIPPacketLayerBuilder(self.ip_address, self.port, self.server_ip, self.server_port)
        print(f"[CLIENT] started on {self.ip_address}:{self.port}")


    def _initialize_processed_count(self):
        if self.variant == "video_demand":
            self.processed = 25
        elif self.variant == "audio_live":
            self.processed = 5
        elif self.variant == "audio_demand":
            self.processed = 13
        elif self.variant == "video_live":
            self.processed = random.randrange(4, 17, 1)


    # Function with main flow of client
    def establish_and_handle_connection(self):

        # UDP - VoIP
        if self.variant == "voip":
            self.basic_filter = self.packet_and_filter_builder.build_basic_filter("udp")
            self._init_voip_call_using_sip()
            self._voip_rtp_transfer()
        # TCP
        else:
            self.basic_filter = self.packet_and_filter_builder.build_basic_filter("tcp")
            self._three_way_handshake()
            self._request_type_of_traffic()
            self.sniff_packets_thread = threading.Thread(target=self._sniff_packets)
            self.sniff_packets_thread.start()
            print("[CLIENT] Sniffing of packets started, starting processing packets.")
            self._process_packets()


    # --------------------------------------------------- TCP ----------------------------------------------------------
    # Function to initiate and start TCP connection with server - 3-way-handshake
    def _three_way_handshake(self):
        print("[CLIENT] Started")
        packet_syn = (IP(dst=self.server_ip,
                         src=self.ip_address) /
                      TCP(dport=self.server_port,
                          sport=self.port,
                          flags="S",
                          seq=self.seq))

        send(packet_syn, verbose=False)
        print(f"[CLIENT] Sent SYN packet to {self.server_ip}:{self.server_port}\n")

        packet_syn_ack = sniff(iface=self.nic,
                       filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.SYN_ACK} != 0)",
                       count=1)[0]

        if packet_syn_ack[TCP].flags == TCPFlags.SYN_ACK:  # SYN-ACK
            print("[CLIENT] Received SYN-ACK packet")
            self.seq = packet_syn_ack[TCP].ack
            self.ack = packet_syn_ack[TCP].seq + 1
            packet_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack)
            time.sleep(0.1)
            send(packet_ack, verbose=False)
            print("[CLIENT] Sent ACK packet")


    # Function for sending request of which type of traffic server should generate and send
    def _request_type_of_traffic(self):
        if self.variant in ["video_demand", "video_live", "audio_live", "audio_demand"]:
            packet_request_type_of_traffic = (self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack) /
                                              Raw(load=self.variant))
            send(packet_request_type_of_traffic, verbose=False)

            ack_type_of_traffic = sniff(iface=self.nic,
                                        filter=self.basic_filter,
                                        count=1, timeout=5)
            while not ack_type_of_traffic:
                send(packet_request_type_of_traffic, verbose=False)
                ack_type_of_traffic = sniff(iface=self.nic,
                                            filter=self.basic_filter,
                                            count=1, timeout=5)

            if ack_type_of_traffic[0].haslayer(TCP) and ack_type_of_traffic[0][TCP].flags == TCPFlags.ACK: #ACK
                self.seq = ack_type_of_traffic[0][TCP].ack
                self.ack = ack_type_of_traffic[0][TCP].seq


    # Function for putting packets to deque,
    # if PSH packet is received it's put to the front of deque
    def _put_packet_to_deque(self, new_packet):
        with self.packet_buffer_lock:
            # Put received PSH packet on top of queue so it's processed first
            if new_packet[TCP].flags == TCPFlags.PSH:
                self.packet_buffer.appendleft(new_packet)
            else:
                self.packet_buffer.append(new_packet)


    # Function to stop sniffing when FIN packet is received
    def _stop_sniffing(self, new_packet):
        if new_packet.haslayer(TCP) and new_packet[TCP].flags == TCPFlags.FIN:
            print("[CLIENT] Received FIN packet, stopping sniffing.\n")
            return True
        if self.stop_generating.is_set():
            return True
        return False


    # Function for sniffing packets and putting them to deque to be processed
    def _sniff_packets(self):
        sniff_filter = self.basic_filter
        sniff(iface=self.nic,
              filter=sniff_filter,
              prn=self._put_packet_to_deque, stop_filter=self._stop_sniffing)


    # Function for processing sniffed packets
    def _process_packets(self):

        print("[CLIENT] Starting processing packets...")
        processed = 0
        time.sleep(5)

        while True:
            packet_received = None

            # Pop packet from deque
            while packet_received is None:

                # End generation if stop generating has been pressed
                if self.stop_generating.is_set():
                    self._teardown_as_initiator()
                    return

                # Pop next packet from deque
                with self.packet_buffer_lock:
                    if self.packet_buffer:
                        packet_received = self.packet_buffer.popleft()

            # Process popped packet
            if packet_received.haslayer(TCP):
                if packet_received.haslayer(Raw): # Carries data
                    # Update ACK
                    if self.ack == packet_received[TCP].seq:
                        self.ack += len(packet_received[Raw].load)
                        processed += 1
                else:
                    # FIN packet
                    if packet_received[TCP].flags == TCPFlags.FIN:
                        self._teardown_as_responder(packet_received)
                        return
                    # ACK packet
                    elif packet_received[TCP].flags == TCPFlags.ACK:
                        self.seq = packet_received[TCP].ack

            # Send ACK after enough packets have been processed, depending on type of communication being generated
            if processed == self.processed:
                packet_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack)
                send(packet_ack, verbose=False)
                if self.variant == "video_live":
                    self.processed = random.randrange(4, 17, 1)
                processed = 0


    # Method to handle end of session and connection when server has initiated end of connection
    def _teardown_as_responder(self, packet_received):
        print("[CLIENT] Received FIN packet, sending FIN-ACK packet")
        # Ak moje posledné poslané ACK menej ako seq vo FIN, ktorý som dostal tak ACK a retransmission
        packet_fin_ack = self.packet_and_filter_builder.build_ip_tcp_packet_layers("FA", packet_received[TCP].ack, packet_received[TCP].seq + 1)
        time.sleep(2)
        send(packet_fin_ack, verbose=False)
        packets = sniff(iface=self.nic,
                       filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                       count=5,
                       timeout=10)
        if packets:
            for packet in packets:
                if packet.haslayer(TCP) and packet[TCP].flags == TCPFlags.ACK:  # packet[TCP].seq == self.seq+1:
                    print("[CLIENT] Received ACK, terminating")
                    if self.socket:
                        self.socket.close()
                        if self.is_generating:
                            self.is_generating.set(False)


    # Method to handle end of connection when initiator is me - client
    def _teardown_as_initiator(self):
        packet_fin = self.packet_and_filter_builder.build_ip_tcp_packet_layers("F", self.seq, self.ack)
        send(packet_fin, verbose=False)
        print("[CLIENT] Sent FIN packet.")

        while True:
            packets = sniff(iface=self.nic,
                            filter=self.basic_filter + f" and (tcp[13] & {TCPFlags.ACK} != 0)",
                            count=1,
                            timeout=5)
            if packets:
                break
            else:
                send(packet_fin, verbose=False)
                print("[CLIENT] Sent FIN packet.")

        if packets[0][TCP].flags == TCPFlags.FIN_ACK:
            print("[CLIENT] Received FIN-ACK, sending ACK and terminating")
            self.seq = packets[0][TCP].ack
            self.ack = self.ack + 1
            packet_fin = self.packet_and_filter_builder.build_ip_tcp_packet_layers("A", self.seq, self.ack)
            time.sleep(2)
            send(packet_fin, verbose=False)
            print("[CLIENT] Sent last ACK packet.")
            if self.socket:
                self.socket.close()
            self.stop_generating.clear()
            if self.is_generating:
                self.is_generating.set(False)


    # ----------------------------------------------- VoIP -------------------------------------------------
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


    def _sniff_packets_voip(self):
        sniff(iface=self.nic,
              filter=self.basic_filter,
              stop_filter=self._stop_sniff_voip)

        if self.stop_by_me:
            self._voip_termination_as_initiator()
        else:
            self._voip_termination_as_responder()


    def _init_voip_call_using_sip(self):
        # Create SIP INVITE
        packet_sip_invite = (self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                             Raw(load=self.sip_packet_layer_builder.build_invite()))
        send(packet_sip_invite, verbose=False)

        packets = sniff(iface=self.nic,
                        filter=self.basic_filter,
                        count=3)

        if packets and len(packets) == 3:
            sip_100 = packets[0]
            sip_180 = packets[1]
            sip_200 = packets[2]

            if sip_100.haslayer(Raw) and sip_180.haslayer(Raw) and sip_200.haslayer(Raw):
                payload_100 = sip_100[Raw].load.decode("utf-8")
                payload_180 = sip_180[Raw].load.decode('utf-8')
                payload_200 = sip_200[Raw].load.decode('utf-8')

                if payload_100.startswith("SIP/2.0 100") and payload_180.startswith("SIP/2.0 180") and payload_200.startswith("SIP/2.0 200"):
                    self.sniff_packets_thread = threading.Thread(target=self._sniff_packets_voip)
                    self.sniff_packets_thread.start()

                    packet_ack = self.packet_and_filter_builder.build_ip_udp_packet_layers() / \
                                 Raw(load=self.sip_packet_layer_builder.build_ack())
                    send(packet_ack, verbose=False)


    # Method for sending voice data in VoIP using RTP protocol
    def _voip_rtp_transfer(self):
        while not self.stop_generating.is_set():

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
                        Raw(rtp_head + rtp_load)
                )

                send(rtp_packet, verbose=False)

                # Update counter variables
                self.timestamp += 160
                self.seq += 1

                # Compute sleep time
                jitter = random.uniform(-0.008, 0.008)
                interval = base_interval + jitter
                next_time += interval
                sleep_duration = next_time - time.perf_counter()
                if sleep_duration > 0:
                    time.sleep(sleep_duration)


    # Method for handling termination of connection and session when stop generating has been pressed on client side
    def _voip_termination_as_initiator(self):
        bye_packet = (self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                      Raw(load=self.sip_packet_layer_builder.build_bye("client")))
        send(bye_packet, verbose=False)

        sip_ok = sniff(iface=self.nic,
                       filter=self.basic_filter,
                       count=1)[0]

        if sip_ok and sip_ok.haslayer(Raw):
            payload_ok = sip_ok[Raw].load.decode('utf-8')
            if payload_ok.startswith("SIP/2.0 200 OK"):
                if self.is_generating:
                    self.is_generating.set(False)

    # Method for handling termination of connection and session when stop generating has been pressed on server side
    def _voip_termination_as_responder(self):
        ok_packet = (self.packet_and_filter_builder.build_ip_udp_packet_layers() /
                     Raw(load=self.sip_packet_layer_builder.build_200_ok("client", None)))

        send(ok_packet, verbose=False)
        if self.is_generating:
            self.is_generating.set(False)