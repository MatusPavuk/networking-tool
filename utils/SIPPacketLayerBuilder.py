class SIPPacketLayerBuilder:

    def __init__(self, source_ip, source_port, remote_ip, remote_port):
        self.source_ip = source_ip
        self.source_port = source_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port


    def build_invite(self):
        return (
            f"INVITE sip:server@{self.remote_ip} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.source_ip}:{self.source_port};branch=z9hG4bK12345\r\n"
            "Max-Forwards: 70\r\n"
            f"From: <sip:client@{self.source_ip}>;tag=1234\r\n"
            f"To: <sip:server@{self.remote_ip}>\r\n"
            f"Call-ID: 11223344@{self.source_ip}\r\n"
            "CSeq: 1 INVITE\r\n"
            f"Contact: <sip:client@{self.source_ip}:{self.source_port}>\r\n"
            "Content-Type: application/sdp\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )
    
    
    def build_ack(self):
        return (
            f"ACK sip:server@{self.remote_ip} SIP/2.0\r\n"
            f"Via: SIP/2.0/UDP {self.source_ip}:{self.source_port};branch=z9hG4bK12345\r\n"
            f"From: <sip:client@{self.source_ip}>;tag=1234\r\n"
            f"To: <sip:server@{self.remote_ip}>;tag=5678\r\n"
            f"Call-ID: 11223344@{self.source_ip}\r\n"
            "CSeq: 1 ACK\r\n"
            f"Contact: <sip:client@{self.source_ip}:{self.source_port}>\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )


    def build_bye(self, source):
        if source == "client":
            return (
                f"BYE sip:server@{self.remote_ip} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP {self.source_ip}:{self.source_port};branch=z9hG4bK12345\r\n"
                f"Max-Forwards: 70\r\n"
                f"From: <sip:client@{self.source_ip}>;tag=1234\r\n"
                f"To: <sip:server@{self.remote_ip}>;tag=5678\r\n"
                f"Call-ID: 11223344@{self.source_ip}\r\n"
                f"CSeq: 2 BYE\r\n"
                f"Content-Length: 0\r\n"
            )
        elif source == "server":
            return (
                f"BYE sip:client@{self.remote_ip} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP {self.source_ip}:{self.source_port};branch=z9hG4bK12345\r\n"
                f"Max-Forwards: 70\r\n"
                f"From: <sip:client@{self.remote_ip}>;tag=1234\r\n"
                f"To: <sip:server@{self.source_ip}>;tag=5678\r\n"
                f"Call-ID: 11223344@{self.remote_ip}\r\n"
                f"CSeq: 2 BYE\r\n"
                f"Content-Length: 0\r\n"
            )
        
        
    def build_100_trying(self):
        return (
            "SIP/2.0 100 Trying\r\n"
            f"Via: SIP / 2.0 / UDP {self.remote_ip}:{self.remote_port};branch=z9hG4bK12345\r\n"
            f"To: <sip:server@{self.source_ip}>\r\n"
            f"From: <sip:client@{self.remote_ip}>;tag=1234\r\n"
            f"Call-ID: 11223344@{self.remote_ip}\r\n"
            "CSeq: 1 INVITE\r\n"
            "Content-Length: 0\r\n"
        )
    
    
    def build_180_ringing(self):
        return (
            "SIP/2.0 180 Ringing\r\n"
            f"Via: SIP/2.0/UDP {self.remote_ip}:{self.remote_port};branch=z9hG4bK12345\r\n"
            f"From: <sip:client@{self.remote_ip}>;tag=1234\r\n"
            f"To: <sip:server@{self.source_ip}>;tag=5678\r\n"
            f"Call-ID: 11223344@{self.remote_ip}\r\n"
            "CSeq: 1 INVITE\r\n"
            f"Contact: <sip:server@{self.source_ip}:{self.source_port}>\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )
    
    
    def build_200_ok(self, source, occasion):
        if source == "client":
            return (
                f"SIP/2.0 200 OK\r\n"
                f"Via: SIP/2.0/UDP {self.remote_ip}:{self.remote_port};branch=z9hG4bK12345\r\n"
                f"From: <sip:server@{self.remote_ip}>;tag=5678\r\n"
                f"To: <sip:client@{self.source_ip}>;tag=1234\r\n"
                f"Call-ID: 11223344@{self.source_ip}\r\n"
                f"CSeq: 2 BYE\r\n"
                f"Content-Length: 0\r\n"
            )
        elif source == "server" and occasion == "invite":
            return (
                "SIP/2.0 200 OK\r\n"
                f"Via: SIP/2.0/UDP {self.remote_ip}:{self.remote_port};branch=z9hG4bK12345\r\n"
                f"From: <sip:client@{self.remote_ip}>;tag=1234\r\n"
                f"To: <sip:server@{self.source_ip}>;tag=5678\r\n"
                f"Call-ID: 11223344@{self.remote_ip}\r\n"
                "CSeq: 1 INVITE\r\n"
                f"Contact: <sip:server@{self.source_ip}:{self.source_port}>\r\n"
                "Content-Type: application/sdp\r\n"
                "Content-Length: 129\r\n"
                "\r\n"
                "v=0\r\n"
                f"o=server 2890844526 2890844526 IN IP4 {self.source_ip}\r\n"
                "s=Session\r\n"
                f"c=IN IP4 {self.source_ip}\r\n"
                "t=0 0\r\n"
                f"m=audio {self.source_port} RTP/AVP 0\r\n"
                "a=rtpmap:0 PCMU/8000\r\n"
            )
        elif source == "server" and occasion == "bye":
            return (
                f"SIP/2.0 200 OK\r\n"
                f"Via: SIP/2.0/UDP {self.remote_ip}:{self.remote_port};branch=z9hG4bK12345\r\n"
                f"From: <sip:client@{self.remote_ip}>;tag=1234\r\n"
                f"To: <sip:server@{self.source_ip}>;tag=5678\r\n"
                f"Call-ID: 11223344@{self.remote_ip}\r\n"
                f"CSeq: 2 BYE\r\n"
                f"Content-Length: 0\r\n"
            )