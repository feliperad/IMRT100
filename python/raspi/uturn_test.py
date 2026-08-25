import imrt_robot_serial
import time
import sys
from collections import deque
from statistics import median

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyUSB0")
except Exception:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()

speed_motor_right = 0 ; speed_motor_left = 200
motor_serial.send_command(speed_motor_left, speed_motor_right)
time.sleep(3)
motor_serial.send_command(0, 0)

print("Goodbye")