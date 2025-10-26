class Network:
    def __init__(self):
        # Maintain lists of connected clients and servers
        self.clients = {}
        self.servers = {}
        self.queue = []  # packet queue

    def register_client(self, client):
        self.clients[client.src_port] = client

    def register_server(self, server):
        self.servers[server.dst_port] = server

    def send_packet(self, bitstring, src_port, dst_port):
        """
        Enqueue the packet instead of delivering immediately.
        """
        self.queue.append({
            'bitstring': bitstring,
            'src_port': src_port,
            'dst_port': dst_port
        })
        print(f"Network: Packet queued from {src_port} to {dst_port}")
        self.process_next()

    def process_next(self):
        """
        Deliver the next packet in the queue.
        """
        if not self.queue:
            print("Network: Queue is empty, nothing to deliver.")
            return

        packet_info = self.queue.pop(0)
        bitstring = packet_info['bitstring']
        src_port = packet_info['src_port']
        dst_port = packet_info['dst_port']

        # Deliver to server
        if dst_port in self.servers:
            server = self.servers[dst_port]
            client = self.clients.get(src_port, None)
            print(f"Network: Delivering packet from {src_port} to server {dst_port}")
            server.receive_packet(bitstring, client, self)
            return

        # Deliver to client
        if dst_port in self.clients:
            client = self.clients[dst_port]
            print(f"Network: Delivering packet from {src_port} to client {dst_port}")
            client.receive_packet(bitstring, self)
            return

        print(f"Network: No device found with port {dst_port}")

    def process_all(self):
        """
        Deliver all packets in the queue sequentially.
        """
        while self.queue:
            self.process_next()
