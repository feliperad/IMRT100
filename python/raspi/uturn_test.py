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

# time.sleep(5)

# while not motor_serial.shutdown_now:
#     speed_motor_right = -200 ; speed_motor_left = 200
#     motor_serial.send_command(speed_motor_left, speed_motor_right)
#     time.sleep(20)
#     motor_serial.send_command(0, 0)

# print("Goodbye")

t0 = time.time()
while not motor_serial.shutdown_now and time.time() - t0 < 20:
    motor_serial.send_command(200, -200)
    time.sleep(0.1)          # 10 Hz, mesma taxa do wall-following

for _ in range(5):
    motor_serial.send_command(0, 0)
    time.sleep(0.05)

print("Goodbye")