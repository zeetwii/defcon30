"""
DEFCON 30 Hack The Microgrid Wind Trubine

This code is intended to be run on the Wind Turbine portion of the workshop
"""
import board # needed for everything
import digitalio # needed for serial
import time # needed for sleep
import neopixel # needed for led control
import struct # needed for serial
import busio # needed for serial

from adafruit_crickit import crickit # needed to talk to crickit
from adafruit_motor import stepper # needed for stepper motor

# For signal control, we'll chat directly with seesaw, use 'ss' to shorted typing!
ss = crickit.seesaw

# set up smoker
smoker = crickit.SIGNAL1    # connect the smoker input to signal I/O #1
ss.pin_mode(smoker, ss.OUTPUT) # make signal pin an output so that we can write to it
ss.digital_write(smoker, False) # when false the smoker is off, when true it is on
smokeTimer = 5 # how long in seconds to run the smoker for

# set up the pump
pump = crickit.drive_1
pump.frequency = 1000
pump.fraction = 0.0

# Setup LEDs
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=1)

# set up serial
#uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=.1)

sysOn = False

while True:
    if sysOn:
        print("System On")
        pump.fraction = 1.0
        ss.digital_write(smoker, True)
        pixels.fill([0,255,0])
        sysOn = False
    else:
        print("System Off")
        pump.fraction = 0.0
        ss.digital_write(smoker, False)
        pixels.fill([255,0,0])
        sysOn = True
    time.sleep(smokeTimer)
