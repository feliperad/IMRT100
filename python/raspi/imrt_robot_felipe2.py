import imrt_robot_serial
import time
import sys

kp = 1
ti = 10
td = 0 #0.01
SP = 35
error_threshold = 10
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
        error==0

    diff_e = (error - previous_error)/execution_period
    int_error += error

    if int_error >= 50:
        int_error = 50
    if int_error <= -50:
        int_error = -50

    print(f'int error is {int_error}')

    if dist_front < front_sensor_threshold:
        speed_motor_left = 0
        speed_motor_right = 100
    else:
        integral_correction = int((1/ti)*int_error)

        if integral_correction >= 50:
            integral_correction = 50
        if integral_correction <= -50:
            integral_correction = -50

        correction = kp*error + integral_correction + td*diff_e

        if correction >=50:
            correction ==50
        elif correction <=-50:
            correction = -50

        speed_motor_right = previous_output + correction

        if speed_motor_right >=150:
            speed_motor_right = 150
        if speed_motor_right <= 50:
            speed_motor_right = 50

        print(f'the previous output is {previous_output} and correction is {correction}')

        if speed_motor_right >=150:
            speed_motor_right ==150
        elif speed_motor_right <=50:
            speed_motor_left = 50

        previous_output = speed_motor_right
        speed_motor_left = 100

    

    print(f'sending commands of {speed_motor_left} and {speed_motor_right}')
    motor_serial.send_command(speed_motor_left, int(speed_motor_right))

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)

print("Goodbye")
