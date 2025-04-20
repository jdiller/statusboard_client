import gc
import time
import sys
import requests
import network
from e7in5v2 import EPD
from credentials import STATUSBOARD_URL
from machine import Pin, SPI, deepsleep, reset, RTC
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

# Initialize RTC memory for persistent storage
rtc = RTC()

# Constants
error_counter = 0
MAX_ERRORS = 10
FULL_REFRESH_INTERVAL = 10  # Do full refresh periodically to clear ghosts
REQUEST_TIMEOUT = 20  # Increased timeout for HTTP requests
SLEEP_TIME_MS = 30000  # Sleep time in milliseconds
MAX_REQUEST_RETRIES = 3  # Number of times to retry a request

# Check RTC memory for refresh counter, initialize if needed
try:
    # Try to read the refresh counter from RTC memory
    refresh_counter = rtc.memory()[0]
    print(f"Loaded refresh counter from RTC memory: {refresh_counter}")
except:
    # If it fails, initialize to -1 to force full refresh on first run
    refresh_counter = 255  # Use 255 to indicate first run
    print(f"Initialized refresh counter: {refresh_counter}")

try:
    # Reset the display first
    e.reset()
    time.sleep(0.1)  # Give it time to stabilize
    # Initialize the display
    e.init()

    # Initialize WiFi
    wlan = network.WLAN(network.WLAN.IF_STA)

    while True:
        if error_counter > MAX_ERRORS:
            print("Error limit reached, resetting device...")
            reset()

        print("Refreshing...")

        # First try to connect via do_connect
        print("Connecting to WiFi...")
        do_connect()  # Call but ignore return value

        # Directly check if we're connected, regardless of what do_connect() returned
        if wlan.isconnected():
            print("WiFi is connected, proceeding...")
            ip = wlan.ifconfig()[0]
            print(f"IP address: {ip}")
        else:
            print("WiFi is not connected, retrying...")
            error_counter += 1
            time.sleep(5)
            continue

        # Connection looks good, try the request with retries
        print(f"Requesting data from {STATUSBOARD_URL}...")
        bitmap = None
        request_success = False

        # Try the request multiple times
        for attempt in range(MAX_REQUEST_RETRIES):
            try:
                print(f"Request attempt {attempt+1}/{MAX_REQUEST_RETRIES}...")
                # Make sure we have enough free memory before request
                gc.collect()

                # Create request with explicit timeout
                r = requests.get(STATUSBOARD_URL, stream=True, timeout=REQUEST_TIMEOUT)
                print("Request successful, reading content...")

                # Get content and clean up immediately
                bitmap = r.content
                r.close()
                del r
                gc.collect()

                request_success = True
                error_counter = 0  # Reset error counter on success
                break  # Exit retry loop on success

            except Exception as ex:
                print(f"Request error on attempt {attempt+1}: {ex}")
                # For error -116 (timeout), wait longer between retries
                if str(ex) == "-116":
                    print("Connection timeout, waiting before retry...")
                    time.sleep(5)
                else:
                    time.sleep(2)

        # If all request attempts failed, continue to next cycle
        if not request_success:
            print("All request attempts failed")
            error_counter += 1
            time.sleep(5)
            continue

        # Turn off WiFi to save power and prevent issues on next cycle
        print("Turning off WiFi...")
        wlan.disconnect()
        wlan.active(False)
        gc.collect()

        if bitmap:
            # Check refresh counter for display update type
            if refresh_counter >= FULL_REFRESH_INTERVAL or refresh_counter == 255:
                print("Doing a full frame refresh...")
                e.display_frame(bitmap)
                # Reset counter to 0 after full refresh
                refresh_counter = 0
            else:
                print(f"Doing a quick frame refresh... (counter: {refresh_counter})")
                e.display_frame_quick(bitmap)
                # Increment counter for next time
                refresh_counter += 1

            # Store updated counter in RTC memory
            print(f"Saving refresh counter to RTC memory: {refresh_counter}")
            rtc.memory(bytes([refresh_counter]))

            bitmap = None
            gc.collect()

        print("Going to sleep...")
        e.sleep()  # Put display to sleep
        # Complete garbage collection before sleep
        gc.collect()
        time.sleep(0.5)  # Longer time to flush IO buffers

        # Use deepsleep for total system reset
        deepsleep(SLEEP_TIME_MS)
finally:
    print("Cleanup...")
    # Try to clean up as much as possible
    try:
        e.sleep()
    except:
        pass
    try:
        spi.deinit()
    except:
        pass
    try:
        wlan.active(False)
    except:
        pass