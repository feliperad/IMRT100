import imrt_robot_serial
import time
import sys

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyUSB0")
except Exception:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()


def kneeTurnCw():
    t0 = time.time()
    while not motor_serial.shutdown_now and time.time() - t0 < 2:
        motor_serial.send_command(200, 0)
        time.sleep(0.1)          # 10 Hz, mesma taxa do wall-following

    for _ in range(5):
        motor_serial.send_command(0, 0)
        time.sleep(0.05)

def kneeTurnCcw():
    t0 = time.time()
    while not motor_serial.shutdown_now and time.time() - t0 < 3:
        motor_serial.send_command(0, 200)
        time.sleep(0.1)          # 10 Hz, mesma taxa do wall-following

    for _ in range(5):
        motor_serial.send_command(0, 0)
        time.sleep(0.05)


kneeTurnCw()
time.sleep(1)
kneeTurnCcw()

print("Goodbye")