import imrt_robot_serial
import time
import sys

min_threshold = 100
median_threshold = 150
max_threshold = 200
front_threshold = 30

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

while not motor_serial.shutdown_now :
    iteration_start_time = time.time()

    dist_front = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    print("Dist front:", dist_front, "   Dist right:", dist_right)


    if dist_front < front_threshold:
        print('Obstacle ahead!')
        speed_motor_right = 100
        speed_motor_left = -100
    else:
        if dist_right <= min_threshold:
            print('too close to the wall!')
            speed_motor_right = 150
            speed_motor_left = 100

        if min_threshold < dist_right < median_threshold:
            print('correct distance!')
            speed_motor_right = 100
            speed_motor_left = 100

        if median_threshold <= dist_right < max_threshold:
            print('little deviation from the wall!')
            speed_motor_right = 100
            speed_motor_left = 150

        if dist_right >= max_threshold:
            print('big deviation from the wall! A turn, maybe?')
            speed_motor_right = -50
            speed_motor_left = 200


    print(f'sending commands of {speed_motor_left} and {speed_motor_right}')
    #motor_serial.send_command(speed_motor_left, int(speed_motor_right))

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)

print("Goodbye")