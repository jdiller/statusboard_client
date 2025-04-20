"""
MicroPython driver for Waveshare 7.5inch e-Paper V2 display
Ported from Waveshare's Arduino driver

MIT License
Copyright (c) 2017 Waveshare, modifications (c) 2025 by @jdiller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from machine import Pin, SPI
import time
from micropython import const

# Display resolution
EPD_WIDTH  = const(800)
EPD_HEIGHT = const(480)

# Display commands
PANEL_SETTING                  = const(0x00)
POWER_SETTING                  = const(0x01)
POWER_OFF                      = const(0x02)
POWER_ON                       = const(0x04)
BOOSTER_SOFT_START             = const(0x06)
DEEP_SLEEP                     = const(0x07)
DATA_START_TRANSMISSION_1      = const(0x10)
DATA_STOP                      = const(0x11)
DISPLAY_REFRESH                = const(0x12)
DATA_START_TRANSMISSION_2      = const(0x13)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
TCON_SETTING                   = const(0x60)
RESOLUTION_SETTING             = const(0x61)
GET_STATUS                     = const(0x71)
AUTO_MEASURE_VCOM              = const(0x80)
VCOM_VALUE                     = const(0x81)
VCM_DC_SETTING                 = const(0x82)

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = Pin(cs, Pin.OUT)
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.busy = Pin(busy, Pin.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        # Initialize voltage values
        self.lut_vcom = bytes([
            0x0, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0xF, 0x1, 0xF, 0x1, 0x2,
            0x0, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        ])

        self.lut_ww = bytes([
            0x10, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x84, 0xF, 0x1, 0xF, 0x1, 0x2,
            0x20, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        ])

        self.lut_bw = bytes([
            0x10, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x84, 0xF, 0x1, 0xF, 0x1, 0x2,
            0x20, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        ])

        self.lut_wb = bytes([
            0x80, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x84, 0xF, 0x1, 0xF, 0x1, 0x2,
            0x40, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        ])

        self.lut_bb = bytes([
            0x80, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x84, 0xF, 0x1, 0xF, 0x1, 0x2,
            0x40, 0xF, 0xF, 0x0, 0x0, 0x1,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        ])

        self.voltage_frame = bytes([0x6, 0x3F, 0x3F, 0x11, 0x24, 0x7, 0x17])

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        time.sleep_ms(delaytime)

    def spi_transfer(self, data):
        self.cs.value(0)
        if type(data) is bytes or type(data) is bytearray:
            self.spi.write(data)
        else:
            self.spi.write(bytes([data]))
        self.cs.value(1)

    def send_command(self, command):
        self.dc.value(0)
        self.spi_transfer(command)

    def send_data(self, data):
        self.dc.value(1)
        self.spi_transfer(data)

    def wait_until_idle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy) == 0):
            self.send_command(GET_STATUS)
            self.delay_ms(20)
        print("e-Paper busy release")

    def reset(self):
        self.digital_write(self.rst, 1)
        self.delay_ms(20)
        self.digital_write(self.rst, 0)
        self.delay_ms(4)
        self.digital_write(self.rst, 1)
        self.delay_ms(20)

    def init(self):
        self.reset()

        # Power settings
        self.send_command(POWER_SETTING)
        self.send_data(0x17)  # 1-0=11: internal power
        self.send_data(self.voltage_frame[6])  # VGH&VGL
        self.send_data(self.voltage_frame[1])  # VSH
        self.send_data(self.voltage_frame[2])  # VSL
        self.send_data(self.voltage_frame[3])  # VSHR

        # VCM DC setting
        self.send_command(VCM_DC_SETTING)
        self.send_data(self.voltage_frame[4])  # VCOM

        # Booster setting
        self.send_command(BOOSTER_SOFT_START)
        self.send_data(0x27)
        self.send_data(0x27)
        self.send_data(0x2F)
        self.send_data(0x17)

        # Power on
        self.send_command(POWER_ON)
        self.delay_ms(100)
        self.wait_until_idle()

        # Panel setting
        self.send_command(PANEL_SETTING)
        self.send_data(0x3F)

        # Resolution setting
        self.send_command(RESOLUTION_SETTING)
        self.send_data(0x03)
        self.send_data(0x20)
        self.send_data(0x01)
        self.send_data(0xE0)

        # Display settings
        self.send_command(0x15)
        self.send_data(0x00)

        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self.send_data(0x10)
        self.send_data(0x00)

        self.send_command(TCON_SETTING)
        self.send_data(0x22)

        # Set resolution
        self.send_command(0x65)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.set_lut()

        return 0

    def set_lut(self):
        self.send_command(0x20)  # VCOM
        for count in range(42):
            self.send_data(self.lut_vcom[count])

        self.send_command(0x21)  # LUTBW
        for count in range(42):
            self.send_data(self.lut_ww[count])

        self.send_command(0x22)  # LUTBW
        for count in range(42):
            self.send_data(self.lut_bw[count])

        self.send_command(0x23)  # LUTWB
        for count in range(42):
            self.send_data(self.lut_wb[count])

        self.send_command(0x24)  # LUTBB
        for count in range(42):
            self.send_data(self.lut_bb[count])

    def display_frame(self, frame_buffer):
        self.send_command(DATA_START_TRANSMISSION_2)
        for i in range(0, len(frame_buffer)):
            self.send_data(frame_buffer[i])

        self.send_command(DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

    def display_frame_quick(self, frame_buffer):
        # This uses a faster version of the full refresh
        # with fewer flashing cycles but still maintaining good image quality
        self.set_quick_lut()  # Set to quick LUT values

        self.send_command(DATA_START_TRANSMISSION_2)
        for i in range(0, len(frame_buffer)):
            self.send_data(frame_buffer[i])

        self.send_command(DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

        # Reset to normal LUT after refresh
        self.set_lut()

    def set_quick_lut(self):
        # This is a quicker version of the full refresh LUT
        # Less flashing but still properly updates the screen
        quick_lut_vcom = bytes([
            0x00, 0x0E, 0x0E, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

        quick_lut_ww = bytes([
            0xA0, 0x0E, 0x0E, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

        quick_lut_bw = bytes([
            0xA0, 0x0E, 0x0E, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

        quick_lut_wb = bytes([
            0x50, 0x0E, 0x0E, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

        quick_lut_bb = bytes([
            0x50, 0x0E, 0x0E, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])

        # Send all the LUT data
        self.send_command(0x20)
        for count in range(42):
            self.send_data(quick_lut_vcom[count])

        self.send_command(0x21)
        for count in range(42):
            self.send_data(quick_lut_ww[count])

        self.send_command(0x22)
        for count in range(42):
            self.send_data(quick_lut_bw[count])

        self.send_command(0x23)
        for count in range(42):
            self.send_data(quick_lut_wb[count])

        self.send_command(0x24)
        for count in range(42):
            self.send_data(quick_lut_bb[count])

    def clear(self):
        self.send_command(DATA_START_TRANSMISSION_2)
        for i in range(self.height * self.width // 8):
            self.send_data(0x00)
        self.send_command(DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

    def sleep(self):
        self.send_command(POWER_OFF)
        self.wait_until_idle()
        self.send_command(DEEP_SLEEP)
        self.send_data(0xA5)