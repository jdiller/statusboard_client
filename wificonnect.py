import network
import machine

SSID = "spatulacity"
KEY = "99th1s991s99th399k3y99"
RETRIES = 20

def do_connect():
    print ("Connecting to wifi")
    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, KEY)
        tries = 0
        while tries < RETRIES:
            if not wlan.isconnected():
                machine.idle()
                tries += 1
            else:
                print("Aborting without connection...")
                break
    print (wlan.ifconfig())