import gc
import time
import sys
import requests
from e7in5v2 import EPD
from credentials import STATUSBOARD_URL
from machine import Pin, SPI, lightsleep

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

try:
    # Reset the display first
    e.reset()
    time.sleep(0.1)  # Give it time to stabilize
    # Initialize the display
    e.init()

    while True:
        print ("refreshing...")
        try:
            r = requests.get(STATUSBOARD_URL, stream=True)
        except Exception as e:
            print (f"Error: {e}")
            lightsleep(5000)
            continue
        bitmap = r.content
        r.close()
        gc.collect()
        print ("Drawing...")
        e.display_frame(bitmap)
        bitmap = None
        gc.collect()
        print ("Sleeping...")
        time.sleep(0.1) #give it pause to flush the io buffer before real device sleep
        lightsleep(30000)
finally:
    print ("Cleanup...")
    e.sleep()
    spi.deinit()