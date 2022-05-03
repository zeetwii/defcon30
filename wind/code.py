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

# Setup LEDs
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=1)

# set up serial
uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=.1)

def initial_setup():
    global pixels, smoker, ss

    print("initial setup")

    # initialize the servo angles
    crickit.continuous_servo_1.throttle = -0
    crickit.servo_2.angle = 90
    crickit.servo_3.angle = 90
    crickit.servo_4.angle = 90

    # initialize the LEDs
    pixels.fill([0,0,255])
    pixels.show()

    #initialize smoker
    ss.digital_write(smoker, False)
    crickit.drive_1.frequency = 1000
    crickit.drive_1.fraction = 0.0  # all the way off

# process serial comms
def process_serial_input():

    if uart.in_waiting >= 6:
        try:
            data = uart.read()

            cmd_msg = struct.unpack("3s", data[:3])[0]
            cmd = "".join([chr(b) for b in cmd_msg])

            # print(len(data))
            # print(cmd)

            if len(data) == 3:
                # return a payload of None
                return (cmd, None)
            else:
                return (cmd, data[3:])

        except:
            print("Serial processing error")
            return None
    else:
        return None

def serial_loop():

    # Check the input buffer prior to any action
    data = process_serial_input()

    if data is not None:

        cmd = data[0]
        payload = data[1]

        if cmd == "led":
            #print("process led cmd")
            pixels[payload[0]] = (payload[1], payload[2], payload[3])
            uart.write("LED \n".encode())
        elif cmd == "top":
            pixels[0] = (payload[0], payload[1], payload[2])
            pixels[1] = (payload[0], payload[1], payload[2])
            pixels[2] = (payload[0], payload[1], payload[2])
            pixels[3] = (payload[0], payload[1], payload[2])
            pixels[4] = (payload[0], payload[1], payload[2])
            uart.write("TOP \n".encode())
        elif cmd == "btm":
            pixels[5] = (payload[0], payload[1], payload[2])
            pixels[6] = (payload[0], payload[1], payload[2])
            pixels[7] = (payload[0], payload[1], payload[2])
            pixels[8] = (payload[0], payload[1], payload[2])
            pixels[9] = (payload[0], payload[1], payload[2])
            uart.write("BTM \n".encode())
        elif cmd == "top":
            pixels[0] = (payload[0], payload[1], payload[2])
            pixels[1] = (payload[0], payload[1], payload[2])
            pixels[2] = (payload[0], payload[1], payload[2])
            pixels[3] = (payload[0], payload[1], payload[2])
            pixels[4] = (payload[0], payload[1], payload[2])
            uart.write("TOP \n".encode())
        elif cmd == "all":
            pixels.fill([payload[0], payload[1], payload[2]])
            uart.write("ALL \n".encode())
        elif cmd == "smk":
            uart.write(f"SMK {str(payload[0])}\n".encode())
            time.sleep(0.1)
            ss.digital_write(smoker, True)
            crickit.drive_1.fraction = 1.0
            time.sleep(int(payload[0]))
            ss.digital_write(smoker, False)
            crickit.drive_1.fraction = 0.0
        elif cmd == "yaw":
            uart.write(f"YAW {str(payload[0])}\n".encode())
            for i in range(int(payload[0])):
                crickit.stepper_motor.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
            crickit.stepper_motor.release()
        elif cmd == "spn":
            uart.write(f"SPN {str(payload[0])}\n".encode())

            crickit.continuous_servo_1.throttle = float(payload[0]) / 100
        elif cmd == "rst":
            initial_setup()
            uart.write("RST \n".encode())
        else:
            uart.write("ERROR, UNKNOWN COMMAND\n".encode())


# Main method that launches everthing
def main():
    initial_setup()
    while True:
        serial_loop()

if __name__ == '__main__':
    main()
