import imrt_robot_serial
import time
import sys

execution_frequency = 10
execution_period = 1. / execution_frequency

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyUSB0")
except:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()

print("Entering loop. Ctrl+c to terminate")

gain_motor_left = 0
gain_motor_right = 0

while not motor_serial.shutdown_now :

    iteration_start_time = time.time()

    dist_left = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    print("Dist left:", dist_left, "   Dist right:", dist_right)

    if 40 < dist_left < 255:
        gain_motor_left = 1
    elif 20 < dist_left < 40:
        gain_motor_left = 2
    elif dist_left < 20:
        gain_motor_left = 3


    if 40 < dist_right < 255:
        gain_motor_right = 1
    elif 20 < dist_right < 40:
        gain_motor_right = 2
    elif dist_right < 20:
        gain_motor_right = 3

    
    speed_motor_left = gain_motor_left * 100
    speed_motor_right = gain_motor_right * 100

    motor_serial.send_command(speed_motor_left, speed_motor_right)

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)

print("Goodbye")
