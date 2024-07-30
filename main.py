from transport.udp import UDPConnection
from dataexport.controller import DataExportController

conn = UDPConnection("192.168.1.1") # Put IP here
controller = DataExportController(conn)

while True:
    print("Numeric", controller._poll(1, 6))
    print("Alert", controller._poll(1, 54))
