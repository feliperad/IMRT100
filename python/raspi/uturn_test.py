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


def kneeTurn():
    t0 = time.time()
    while not motor_serial.shutdown_now and time.time() - t0 < 1.80:
        motor_serial.send_command(200, 0)
        time.sleep(0.1)          # 10 Hz, mesma taxa do wall-following

    for _ in range(5):
        motor_serial.send_command(0, 0)
        time.sleep(0.05)


kneeTurn()

print("Goodbye")