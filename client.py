from packet import TCPPacket

class TCPClient:
    def __init__(self, src_port):
        self.src_port = src_port
        self.seq_num = 1000        # initial sequence number (can be random)
        self.ack_num = 0         # will store last ACK received
        self.state = 'CLOSED'

    def create_packet(self, flags, payload="", dst_port=0):
        """
        Helper method to create a TCPPacket from client info.
        Pass dst_port explicitly when creating a packet to send.
        """
        return TCPPacket(
            src_port=self.src_port,
            dst_port=dst_port,
            seq_num=self.seq_num,
            ack_num=self.ack_num,
            flags=flags,
            payload=payload
        )

    def update_state(self, packet, outgoing=False):
        if outgoing:
            # Outgoing state transitions
            if packet.flags.get('SYN', 0) and not packet.flags.get('ACK', 0) and self.state == 'CLOSED':
                self.state = 'SYN-SENT'
            elif packet.flags.get('FIN', 0) and self.state == 'ESTABLISHED':
                self.state = 'FIN-WAIT-1'
        else:
            # Incoming state transitions
            if packet.flags.get('SYN', 0) and packet.flags.get('ACK', 0):
                self.state = 'SYN-ACK-RECEIVED'
                self.ack_num = packet.seq_num + 1
            elif packet.flags.get('ACK', 0) and self.state == 'SYN-ACK-RECEIVED':
                self.state = 'ESTABLISHED'
            elif packet.flags.get('PSH', 0):
                self.state = 'DATA-RECEIVED'
                self.ack_num = packet.seq_num + len(packet.payload)
            elif packet.flags.get('ACK', 0) and self.state == 'FIN-WAIT-1':
                self.state = 'FIN-WAIT-2'
            elif packet.flags.get('FIN', 0):
                # Respond to server FIN
                self.ack_num = packet.seq_num + 1
                self.state = 'TIME-WAIT'

    def send_data(self, payload, dst_port, network):
        if self.state != 'ESTABLISHED':
            print("Connection not established yet!")
            return

        packet = self.create_packet(flags={'ACK': 1, 'PSH': 1}, payload=payload, dst_port=dst_port)
        packet.seq_num = self.seq_num  # send current sequence number
        self.send_packet(packet, network)
        self.seq_num += len(payload)  # increment seq_num by payload length

    def terminate_connection(self, dst_port, network):
        print("Client initiating termination")
        fin_packet = self.create_packet(flags={'FIN': 1, 'ACK': 1}, dst_port=dst_port)
        self.send_packet(fin_packet, network)
        print("Client → Sent FIN")

    def send_packet(self, packet, network):
        # ensure dst_port is set on the packet (caller should have set it)
        if packet.dst_port == 0:
            raise ValueError("Destination port not set on packet before sending")
        bitstring = packet.to_bits()
        self.update_state(packet, outgoing=True)
        print(f"Client sending packet: {packet}")
        network.send_packet(bitstring, self.src_port, packet.dst_port)

    def receive_packet(self, bitstring, network):
        """
        Reconstruct packet from bits and process it.
        This signature matches Network.send_packet's call for client destinations.
        """
        packet = TCPPacket.from_bits(bitstring)
        print(f"Client received packet: {packet}")

        self.update_state(packet)

        # If the server sends SYN+ACK
        if packet.flags.get('SYN', 0) and packet.flags.get('ACK', 0):
            if self.state != 'ESTABLISHED':
                # set ack to server seq + 1
                self.ack_num = packet.seq_num + 1
                # send final ACK to complete handshake
                ack_packet = self.create_packet(flags={'ACK': 1}, dst_port=packet.src_port)
                self.send_packet(ack_packet, network)
                self.state = 'ESTABLISHED'
                print("Client → Sent ACK to complete handshake")

        # For any pure ACKs (later data exchange)
        elif packet.flags.get('ACK', 0):
            self.ack_num = packet.seq_num + 1
            print("Client → ACK received and processed")

        # Server sent FIN
        if packet.flags.get('FIN', 0):
            ack_packet = self.create_packet(flags={'ACK': 1}, dst_port=packet.src_port)
            self.send_packet(ack_packet, network)
            self.state = 'TIME-WAIT'
            print("Client → Sent ACK for server FIN, state TIME-WAIT")


