import imrt_robot_serial
import time
import sys
import math

gain_motor_left = 0
gain_motor_right = 0

kp = 1
ti = 100
td = 0.01
SP = 20
error_threshold = 5
front_sensor_threshold = 6
previous_output = 100

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

previous_error = 0
int_error = 0

while not motor_serial.shutdown_now :

    iteration_start_time = time.time()

    dist_front = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    print("Dist front:", dist_front, "   Dist right:", dist_right)

    error = SP - dist_right

    if -1* error_threshold <= error <= error_threshold:
        error ==0

    diff_e = (error - previous_error)/execution_period
    int_error += error

    if dist_front < front_sensor_threshold:
        speed_motor_left = 0
        speed_motor_right = 100
    else:
        correction = kp*error + int((1/ti)*int_error + td*diff_e)

        if correction >=100:
            correction ==100
        elif correction <= 0:
            correction = 0

        speed_motor_left = previous_output + correction
        previous_output = speed_motor_left
        speed_motor_right = 100

    print(f'right motor value: {speed_motor_right}, error is {error}')
    print(f' previous output is {previous_output}, integral action is {int((1/ti)*int_error)} ')


    motor_serial.send_command(speed_motor_left, speed_motor_right)

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)

print("Goodbye")
