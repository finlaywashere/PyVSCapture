import datetime
from avaparser import parse_value, parse_u16, parse_u32

class DataExportController:

    def __init__(self, transport):
        """
        Initializes the controller and sends a MDS create event response
        Transport is a reference to a UDP or serial transport class
        """
        self._transport = transport
        self._mds_create()

    def _recv_packet(self):
        """
        Reads a data export protocol packet from the underlying transport mechanism

        This may be wrong as there are multiple length fields and they are confusing
        """
        header = self._transport.recv(8)
        data = []
        data += header
        # u16 session_id, u16 context_id, u16 ro_type, u16 length
        length = parse_u16(header, 6)
        data += self._transport.recv(length)
        return data

    def _send(self, data):
        """
        Helper function to pass data to the transport layer
        """
        self._transport.send(data)

    def _mds_create(self):
        """
        Processes a MDS create event and sends back a mds create event result to finish association
        """
        mds_create_event = self._recv_packet()
        # Invoke id is the 5th u16 in the header
        # header[8] and [9] contain invoke id
        managed_object = mds_create_event[14:20] # Slice out the 6 byte managed object info from event report argument
        self._managed_object = managed_object
        response = [
                    0xE1, 0x00, 0x00, 0x02, # SPpdu
                    0x00, 0x02, 0x00, 0x14, # ROapdus
                    mds_create_event[8], mds_create_event[9], 0x00, 0x01, 0x00, 0x0E, # RORSapdu
                    ]
        response += managed_object
        response += [0x00, 0x00, 0x00, 0x00, 0x0D, 0x06, 0x00, 0x00 # Event report, set relative time to 0
                     ]
        self._epoch = datetime.datetime.now()
        self._send(response)
        self._poll_number = 0

    def _decode_poll_data(self, result):
        # Timestamp starts at index 25 and is u32
        rel_timestamp = result[25] << 24 | result[26] << 16 | result[27] << 8 | result[28]
        # Actual data starts after 46 bytes (index 45)
        count = result[45] << 8 | result[46] # Poll info count
        index = 48
        data = []
        for i in range(count): # Loop through all SingleContextPoll's
            index += 2 # Skip over mds context
            poll_count = result[index] << 8 | result[index + 1]
            index += 4 # Skip over count and length
            context_data = []
            for j in range(poll_count): # Loop through all ObservationPoll's
                handle = result[index] << 8 | result[index + 1]
                index += 2
                ava_count = result[index] << 8 | result[index + 1] # Count of Attribute Value Assertions within Observation Poll
                index += 4 # Skip over count and length
                observation_data = []
                for k in range(ava_count): # Loop through AVA's
                    attr = parse_value(result[index:])
                    index += 4 + attr[1]
                    observation_data.append(attr)
                context_data.append(observation_data)
            data.append(context_data)


    def _poll(self, partition, code):
        """
        Internal function to send a poll request with a given type to the device
        """
        request = [0xE1, 0x00, 0x00, 0x02, # SPpdu
                   0x00, 0x01, 0x00, 0x1C, # ROapdus
                   0x00, 0x01, 0x00, 0x07, 0x00, 0x16, # ROIVapdu
                   ]
        request += self._managed_object
        request += [0x00, 0x00, 0x00, 0x00, 0x0c, 0x16, 0x00, 0x08, # Action argument
                    (self._poll_number >> 8) & 0xFF, self._poll_number & 0xFF, partition >> 8, partition & 0xFF, code >> 8, code & 0xFF, 0x00, 0x00, # Poll request info
                    ]
        self._send(request)
        result = self._recv_packet()
        if result[5] == 0x02:
            # Single result
            rel_time = parse_u32(result, 26)
            data = self._decode_poll_data(result[46:])
            return (rel_time, data)
        else:
            # Linked result
            rel_time = parse_u32(result, 26)
            data = []
            for i in range(10): # timeout after 10 packets
                if result[5] == 0x02:
                    break
                data += self._decode_poll_data(result[46:])
                result = self._recv_packet()
            return (rel_time, data)
