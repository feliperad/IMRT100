# Example code for IMRT100 robot project

# Import some modules that we need
import imrt_robot_serial
import time
import sys

execution_frequency = 10 #Hz
execution_period = 1. / execution_frequency #seconds

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyUSB0")
except:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()


print("Entering loop. Ctrl+c to terminate")

while not motor_serial.shutdown_now :

    iteration_start_time = time.time() # Get the current time

    dist_left = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    print("Dist left:", dist_left, "   Dist right:", dist_right)

    gain = 0
    speed_motor_left = dist_right * gain
    speed_motor_right = dist_left * gain

    motor_serial.send_command(speed_motor_left, speed_motor_right)

    iteration_end_time = time.time() # current time
    iteration_duration = iteration_end_time - iteration_start_time # time spent executing code
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)

print("Goodbye")
