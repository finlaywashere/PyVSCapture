import socket

import udpconstants as constants

class UDPConnection:
    """
    Connects to a target device over port 24105
    """
    def __init__(self, ip, port=24105)
        self._socket = socket.socket(socket.AF_INET, socker.SOCK_DGRAM)
        self._socket.settimeout(1.0)
        self._remote = (ip, port)
        self._associate()

    def cleanup(self):
        self._disassociate()

    def send(self, data):
        """
        Sends a UDP packet to the remote device with arbitrary data.
        Just a helper function for other calls
        """
        self._socket.sendto(bytearray(data), self._remote)

    def recv(self, count):
        """
        Receives a UDP packet with a given size
        Just a helper function for other calls
        """
        return self._socket.recvfrom(count)[0]

    def _recv_packet(self):
        """
        Receives a full packet from the device
        """
        header = self.recv(2)
        data = []
        data += header
        if header[1] == 0xFF:
            len_bytes = self.recv(2)
            data += len_bytes
            length = len_bytes[0] << 8 | len_bytes[1]
            data += self.recv(length)
        else:
            data += self.recv(header[1])
        return data

    def _associate(self) -> bool:
        """
        Sets up communication with the device
        """
        self.send(constants.ASSOCIATE)
        # We're assuming that if its successful we have negotiated the options we selected (only sent 1 option)
        # Header flags: 0x0E = Success, 0x0C = Refuse
        header = self._recv_packet()
        if header[0] == 0x0E: # Check for success
            return True
        return False

    def _disassociate(self) -> bool:
        """
        Ends a session with the device
        """
        self.send(constants.RELEASE)
        # Header flags: 0x0A = Success
        header = self._recv_packet()
        if header[0] == 0x0A:
            return True
        return False

