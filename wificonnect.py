import network
import machine
import time
from credentials import SSID, KEY
RETRIES = 20

def do_connect():
    """Connect to WiFi and return True if successful, False otherwise"""
    print("Setting up WiFi...")

    # Get the WiFi interface
    wlan = network.WLAN(network.WLAN.IF_STA)

    # First, make sure it's active
    if not wlan.active():
        print("Activating WiFi interface...")
        wlan.active(True)
        time.sleep(1)

    # Check if already connected
    if wlan.isconnected():
        print("Already connected to WiFi")
        print(wlan.ifconfig())
        return True

    # Not connected, need to establish connection
    print(f"Connecting to SSID: {SSID}")

    try:
        # Disconnect first in case we're in a half-connected state
        wlan.disconnect()
        time.sleep(1)

        # Try to connect
        wlan.connect(SSID, KEY)

        # Wait for connection
        for i in range(RETRIES):
            if wlan.isconnected():
                ip = wlan.ifconfig()[0]
                print(f"Connected! IP: {ip}")
                return True

            print(f"Waiting for connection... ({i+1}/{RETRIES})")
            time.sleep(1)

        # If we get here, connection timed out
        print("Connection timed out")
        return False

    except Exception as ex:
        print(f"Connection error: {ex}")
        return False
