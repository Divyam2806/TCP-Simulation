# sim.py
from client import TCPClient
from server import TCPServer
from network import Network

# --- Initialize network, client, server ---
network = Network()
client = TCPClient(src_port=12345)
server = TCPServer(dst_port=80)

network.register_client(client)
network.register_server(server)

# --- Step 1: Client sends SYN to initiate handshake ---
syn_packet = client.create_packet(flags={'SYN': 1}, dst_port=80)
client.send_packet(syn_packet, network)
print("\n[Simulation] Client → Sent SYN")

# --- Step 2: Process queued packets (SYN delivered to server) ---
# network.process_all()

# --- Step 3: Process queued packets (SYN+ACK delivered back to client) ---
# network.process_all()

# --- Step 4: Process queued packets (final ACK from client to server) ---
# network.process_all()

# At this point, handshake should be complete
print("\n[Simulation] Handshake completed.")
print(f"Client state: {client.state}")
print(f"Server state: {server.state}")

# --- Step 5: Client sends data ---
data_packet = client.create_packet(flags={'ACK': 1, 'PSH': 1},
                                   payload="Hello Server!",
                                   dst_port=80)
client.send_packet(data_packet, network)
print("\n[Simulation] Client → Sent data packet")

# --- Step 6: Process all queued packets (data delivered to server) ---
# network.process_all()

# --- Step 7: Process any ACKs sent back to client ---
# network.process_all()

print("\n[Simulation] Data transfer complete.")
print(f"Client state: {client.state}")
print(f"Server state: {server.state}")
