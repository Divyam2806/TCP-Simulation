from packet import TCPPacket

class TCPServer:
    def __init__(self, dst_port):
        # The port the server listens on
        self.dst_port = dst_port
        self.seq_num = 5000       # initial sequence number for server
        self.ack_num = 0          # last ACK sent/expected
        self.state = 'LISTENING'
        self.pending_fin = False

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
            if packet.flags.get('FIN', 0):
                if self.state == 'ESTABLISHED':
                    self.state = 'FIN-WAIT-1'
                elif self.state == 'CLOSE-WAIT':
                    self.state = 'LAST-ACK'
            return

        # Incoming packets
        if self.state == 'LISTENING' and packet.flags.get('SYN', 0):
            self.state = 'SYN-RECEIVED'
        elif self.state == 'SYN-RECEIVED' and packet.flags.get('ACK', 0):
             self.state = 'ESTABLISHED'
        elif self.state in ['ESTABLISHED', 'DATA-RECEIVED'] and packet.flags.get('PSH', 0):
            self.state = 'DATA-RECEIVED'
        elif self.state == 'FIN-WAIT-1' and packet.flags.get('ACK', 0):
            self.state = 'FIN-WAIT-2'
        elif packet.flags.get('FIN', 0):
            if self.state == 'ESTABLISHED':
                self.state = 'CLOSE-WAIT'
            elif self.state == 'FIN-WAIT-2':
                self.state = 'TIME-WAIT'
        print(f"Server state changed to {self.state}")

    def receive_packet(self, bitstring, client, network):
        """
        Called by Network when packet arrives at this server.
        signature: (bitstring, client_object_or_None, network)
        """
        packet = TCPPacket.from_bits(bitstring)
        print(f"Server received packet: {packet}")

        self.update_state(packet)

        # Handle SYN
        if self.state == 'SYN-RECEIVED':
            response_flags = {'SYN': 1, 'ACK': 1}
            response = self.create_packet(response_flags, dst_port=packet.src_port)
            self.send_packet(response, network)
            return

        # Handle Data
        if self.state in ['ESTABLISHED', 'DATA-RECEIVED'] and packet.flags.get('PSH', 0):
            self.ack_num = packet.seq_num + len(packet.payload)
            print(f"Server received data: {packet.payload}")
            ack_packet = self.create_packet({'ACK': 1}, dst_port=packet.src_port)
            self.send_packet(ack_packet, network)
            return

        # Handle FIN from client
        if packet.flags.get('FIN', 0):
            print("Server received FIN")
            # Update ack_num properly
            self.ack_num = packet.seq_num + 1
            if self.state in ['ESTABLISHED', 'DATA-RECEIVED']:
                self.state = 'CLOSE-WAIT'
            print(f"Server state changed to {self.state}")

            # Step 1: send ACK for client FIN
            ack_packet = self.create_packet({'ACK': 1}, dst_port=packet.src_port)
            self.send_packet(ack_packet, network)
            print("Server → Sent ACK for FIN")

            # Step 2: set flag to send FIN in the next simulation step
            self.pending_fin = True
            return

        # Send FIN if pending
        if getattr(self, 'pending_fin', False):
            fin_packet = self.create_packet({'FIN': 1}, dst_port=packet.src_port)
            self.seq_num += 1  # increment server sequence number
            self.send_packet(fin_packet, network)
            print("Server → Sent FIN")
            self.state = 'LAST-ACK'
            self.pending_fin = False
            return

        # Handle final ACK from client for server FIN
        if packet.flags.get('ACK', 0) and self.state == 'LAST-ACK':
            if packet.ack_num == self.seq_num:
                self.state = 'CLOSED'
                print("Server state CLOSED")

    def send_packet(self, packet, network):
        bitstring = packet.to_bits()
        print(f"Server sending packet: {packet}")
        self.update_state(packet, outgoing=True)
        # src_port for server-originated packet is the server's listening port
        network.send_packet(bitstring, self.dst_port, packet.dst_port)
