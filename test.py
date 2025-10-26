from packet import TCPPacket

pkt = TCPPacket(5000, 80, 100, 0, flags={'SYN':1})
print(pkt)
print(pkt.to_bits())
print(TCPPacket.from_bits(pkt.to_bits()))