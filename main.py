import gc
import time
import sys
import requests
import network
from e7in5v2 import EPD
from credentials import STATUSBOARD_URL
from machine import Pin, SPI, lightsleep, reset
from wificonnect import do_connect

# Define SPI Pins (Using VSPI)
mosi = Pin(14, Pin.OUT)  # SPI MOSI (DIN)
miso = Pin(12, Pin.IN)   # Not really needed for this display
clk = Pin(13, Pin.OUT)   # SPI SCK
cs = Pin(15, Pin.OUT)    # Chip Select
dc = Pin(27, Pin.OUT)    # Data/Command
rst = Pin(26, Pin.OUT)   # Reset
busy = Pin(25, Pin.IN)   # Busy signal

spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=clk, mosi=mosi, miso=miso)
# Create EPD instance
e = EPD(spi, cs, dc, rst, busy)

error_counter = 0
MAX_ERRORS = 10
refresh_counter = -1
FULL_REFRESH_INTERVAL = 3  # Do full refresh every 3 updates

try:
    wlan = network.WLAN(network.WLAN.IF_STA)
    if not wlan.isconnected():
        do_connect()
    # Reset the display first
    e.reset()
    time.sleep(0.1)  # Give it time to stabilize
    # Initialize the display
    e.init()

    while True:
        if error_counter > MAX_ERRORS:
            print("Error limit reached, resetting device...")
            reset()
        print ("refreshing...")
        try:
            r = requests.get(STATUSBOARD_URL, stream=True)
        except Exception as ex:
            error_counter += 1
            print (f"Error: {ex}")
            print ("Trying to reconnect wifi...")
            do_connect()
            time.sleep(0.1) #give it pause to flush the io buffer before real device sleep
            lightsleep(3000)
            continue
        error_counter = 0
        bitmap = r.content
        r.close()
        gc.collect()
        print ("Drawing...")
        # Do a full refresh every FULL_REFRESH_INTERVAL updates to prevent ghosting
        if refresh_counter >= FULL_REFRESH_INTERVAL or refresh_counter == -1:
            e.display_frame(bitmap)
            refresh_counter = 0
        else:
            e.display_frame_quick(bitmap)
            refresh_counter += 1
        bitmap = None
        gc.collect()
        print ("Sleeping...")
        time.sleep(0.1) #give it pause to flush the io buffer before real device sleep
        lightsleep(30000)
finally:
    print ("Cleanup...")
    e.sleep()
    spi.deinit()