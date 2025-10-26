class TCPPacket:
    def __init__(self, src_port, dst_port, seq_num, ack_num, flags=None,
                 window_size=0, checksum=0, urgent_pointer=0, payload=""):
        self.src_port = src_port  # 16-bit
        self.dst_port = dst_port  # 16-bit
        self.seq_num = seq_num  # 32-bit
        self.ack_num = ack_num  # 32-bit
        self.data_offset = 5  # 4-bit, default 5 (20 bytes header)
        self.reserved = 0  # 3-bit, default 0
        # Keep flags as dict with keys URG, ACK, PSH, RST, SYN, FIN
        self.flags = flags or {'URG': 0, 'ACK': 0, 'PSH': 0,
                               'RST': 0, 'SYN': 0, 'FIN': 0}
        self.window_size = window_size  # 16-bit
        self.checksum = checksum  # 16-bit
        self.urgent_pointer = urgent_pointer  # 16-bit
        self.payload = payload  # variable-length string

    def __str__(self):
        """Human-readable summary of packet"""
        flag_str = ','.join([ k + '=1' for k, v in self.flags.items() if v])
        return (f"SRC={self.src_port}, DST={self.dst_port}, SEQ={self.seq_num}, "
                f"ACK={self.ack_num}, FLAGS={flag_str}, WIN={self.window_size}, "
                f"CHK={self.checksum}, URG_PTR={self.urgent_pointer}, "
                f"DATA={self.payload}")

    def to_bits(self):
        """Convert the TCPPacket into a bitstring (header + payload)"""
        src_bits = format(self.src_port, '016b')
        dst_bits = format(self.dst_port, '016b')
        seq_bits = format(self.seq_num, '032b')
        ack_bits = format(self.ack_num, '032b')
        offset_bits = format(self.data_offset, '04b')
        reserved_bits = format(self.reserved, '03b')

        # Convert flags dictionary to 6-bit string (URG, ACK, PSH, RST, SYN, FIN)
        flag_order = ['URG', 'ACK', 'PSH', 'RST', 'SYN', 'FIN']
        flags_bits_6 = ''.join(str(self.flags.get(f, 0)) for f in flag_order)
        # Add 3 extra reserved bits to make the 9-bit field
        flags_bits = flags_bits_6 + '000'  # total 9 bits

        window_bits = format(self.window_size, '016b')
        checksum_bits = format(self.checksum, '016b')
        urgent_bits = format(self.urgent_pointer, '016b')

        payload_bits = ''.join(format(ord(ch), '08b') for ch in self.payload)

        bitstring = (src_bits + dst_bits + seq_bits + ack_bits +
                     offset_bits + reserved_bits + flags_bits +
                     window_bits + checksum_bits + urgent_bits + payload_bits)

        return bitstring

    @classmethod
    def from_bits(cls, bitstring):
        """
        Reconstruct a TCPPacket from a bitstring.
        Assumes the same field order used in to_bits().
        """
        if len(bitstring) < 160:
            raise ValueError("Bitstring too short to contain full TCP header (160 bits)")

        src_port = int(bitstring[0:16], 2)
        dst_port = int(bitstring[16:32], 2)
        seq_num = int(bitstring[32:64], 2)
        ack_num = int(bitstring[64:96], 2)
        data_offset = int(bitstring[96:100], 2)
        reserved = int(bitstring[100:103], 2)

        # Extract the full 9-bit flags field, then consider the first 6 bits as URG..FIN
        flags_bits_full = bitstring[103:112]  # indices 103..111 inclusive => 9 bits
        flag_order = ['URG', 'ACK', 'PSH', 'RST', 'SYN', 'FIN']
        flags = {flag_order[i]: int(flags_bits_full[i]) for i in range(6)}

        window_size = int(bitstring[112:128], 2)
        checksum = int(bitstring[128:144], 2)
        urgent_pointer = int(bitstring[144:160], 2)

        payload_bits = bitstring[160:]
        payload = ''
        if payload_bits:
            # pad/truncate to whole bytes if needed (should be whole bytes from to_bits)
            for i in range(0, len(payload_bits), 8):
                byte = payload_bits[i:i + 8]
                if len(byte) < 8:
                    # ignore incomplete trailing bits
                    continue
                payload += chr(int(byte, 2))

        return cls(src_port, dst_port, seq_num, ack_num, flags,
                   window_size, checksum, urgent_pointer, payload)
