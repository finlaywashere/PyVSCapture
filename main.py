from transport.udp import UDPConnection
from dataexport.controller import DataExportController
import time

conn = UDPConnection("10.0.0.238") # Put IP here
controller = DataExportController(conn)

while True:
    print("Numeric", controller._poll(1, 6))
    print("Alert", controller._poll(1, 54))
    time.sleep(1)
