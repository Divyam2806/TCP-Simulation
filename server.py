from packet import TCPPacket

class TCPServer:
    def __init__(self, dst_port):
        # The port the server listens on
        self.dst_port = dst_port
        self.seq_num = 5000       # initial sequence number for server
        self.ack_num = 0          # last ACK sent/expected
        self.state = 'LISTENING'

    def create_packet(self, flags, payload="", dst_port=0):
        """
        Helper to create a TCPPacket from server info.
        dst_port should be the client's port when sending.
        """
        return TCPPacket(
            src_port=self.dst_port,
            dst_port=dst_port,
            seq_num=self.seq_num,
            ack_num=self.ack_num,
            flags=flags,
            payload=payload
        )

    def update_state(self, packet, outgoing=False):
        """
        Update server state based on incoming or outgoing packet.
        outgoing=True is for packets server itself sends (not strictly needed now)
        """
        if outgoing:
            # Can be used later for server-originated state changes
            return

        # Handshake transitions
        if self.state == 'LISTENING' and packet.flags.get('SYN', 0):
            self.state = 'SYN-RECEIVED'
            print(f"Server state changed to {self.state}")
        elif self.state == 'SYN-RECEIVED' and packet.flags.get('ACK', 0):
            self.state = 'ESTABLISHED'
            print(f"Server state changed to {self.state}")
        # Data received only after handshake complete
        elif self.state == 'ESTABLISHED' and packet.flags.get('PSH', 0):
            self.state = 'DATA-RECEIVED'
            self.ack_num = packet.seq_num + len(packet.payload)
            print(f"Server state changed to {self.state}")

    def receive_packet(self, bitstring, client, network):
        """
        Called by Network when packet arrives at this server.
        signature: (bitstring, client_object_or_None, network)
        """
        packet = TCPPacket.from_bits(bitstring)
        print(f"Server received packet: {packet}")

        self.update_state(packet)

        if self.state == 'SYN-RECEIVED':
            response_flags = {'SYN': 1, 'ACK': 1}
            response = self.create_packet(response_flags, dst_port=packet.src_port)
            network.send_packet(response.to_bits(), self.dst_port, packet.src_port)

        elif self.state == 'DATA-RECEIVED':
            print(f"Server received data: {packet.payload}")
            ack_packet = self.create_packet({'ACK': 1}, dst_port=packet.src_port)
            network.send_packet(ack_packet.to_bits(), self.dst_port, packet.src_port)

    def send_packet(self, packet, network):
        bitstring = packet.to_bits()
        print(f"Server sending packet: {packet}")
        self.update_state(packet)
        # src_port for server-originated packet is the server's listening port
        network.send_packet(bitstring, self.dst_port, packet.dst_port)
