import gc
import time
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
try:
    spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=clk, mosi=mosi, miso=miso)
    # Create EPD instance
    e = EPD(spi, cs, dc, rst, busy)
    # Reset the display first
    e.reset()
    time.sleep(0.1)  # Give it time to stabilize
    # Initialize the display
    e.init()

    while True:
        print ("refreshing...")
        r = requests.get(STATUSBOARD_URL, stream=True)
        bitmap = r.content
        r.close()
        gc.collect()
        gc.collect()
        print ("Drawing...")
        e.display_frame(bitmap)
        bitmap = None
        gc.collect()
        print ("Sleeping...")
        lightsleep(30000)
finally:
    print ("Cleanup...")
    e.sleep()
    spi.deinit()