import network
import socket
import ssl
import time
from machine import Pin, ADC

SSID = "HU-StDev"
PASSWORD = "Zf*03363380192"

# 1. Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
while not wlan.isconnected():
    time.sleep(0.5)
ip = wlan.ifconfig()[0]

# 2. Load DER certificates
with open("key.der", "rb") as f:
    key = f.read()
with open("cert.der", "rb") as f:
    cert = f.read()

# 3. Configure SSL Context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(cert, key)

# 4. Initialize Sensor (Example: Onboard Temperature Sensor)
sensor = ADC(4)

def read_sensor():
    reading = sensor.read_u16() * (3.3 / 65535)
    temp_c = 27 - (reading - 0.706) / 0.001721
    return round(temp_c, 2)

# 5. Start HTTPS Socket Server
addr = socket.getaddrinfo("0.0.0.0", 443)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)

while True:
    cl, _ = s.accept()
    try:
        cl_ssl = context.wrap_socket(cl, server_side=True)
        request = cl_ssl.recv(1024)
        
        payload = f'{{"temperature_c": {read_sensor()}}}'
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            "Connection: close\r\n\r\n"
            f"{payload}"
        )
        cl_ssl.write(response.encode("utf-8"))
        cl_ssl.close()
    except Exception:
        cl.close()