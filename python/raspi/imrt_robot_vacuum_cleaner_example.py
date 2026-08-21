import imrt_robot_serial
import time
import sys
import random

LEFT = -1
RIGHT = 1
FORWARDS = 1
BACKWARDS = -1
DRIVING_SPEED = 100
TURNING_SPEED = 100
STOP_DISTANCE = 25

def stop_robot(duration):

    iterations = int(duration * 10)
    
    for i in range(iterations):
        motor_serial.send_command(0, 0)
        time.sleep(0.10)


def drive_robot(direction, duration):
    
    speed = DRIVING_SPEED * direction
    iterations = int(duration * 10)

    for i in range(iterations):
        motor_serial.send_command(speed, speed)
        time.sleep(0.10)


def turn_robot_random_angle():

    direction = random.choice([-1,1])
    iterations = random.randint(10, 25)
    
    for i in range(iterations):
        motor_serial.send_command(TURNING_SPEED * direction, -TURNING_SPEED * direction)
        time.sleep(0.10)

execution_frequency = 10 # We want our program to send commands at 10 Hz (10 commands per second)
execution_period = 1. / execution_frequency #seconds
motor_serial = imrt_robot_serial.IMRTRobotSerial() # Create motor serial object

# Open serial port. Exit if serial port cannot be opened
try:
    motor_serial.connect("/dev/ttyACM0")
except:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

# Start serial receive thread
motor_serial.run()

print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now :

    dist_1 = motor_serial.get_dist_1()
    dist_2 = motor_serial.get_dist_2()
    print("Dist 1:", dist_1, "   Dist 2:", dist_2)

    
    if dist_1 < STOP_DISTANCE or dist_2 < STOP_DISTANCE:
        print("Obstacle!")
        stop_robot(1)
        drive_robot(BACKWARDS, 0.5)
        turn_robot_random_angle()
    else:
        
        drive_robot(FORWARDS, 0.1)

print("Goodbye")
