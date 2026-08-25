import imrt_robot_serial
import time
import sys
from collections import deque
from statistics import median

kp = 2
min_threshold = 10
median_threshold = 20
max_threshold = 50
front_threshold = 5
previous_output = 50

execution_frequency = 10
execution_period = 1. / execution_frequency

DIST_MIN = 1.0
DIST_MAX = 255.0
EMERGENCY_ON_RAW = True   # parada de emergencia usa leitura crua (sem lag)

class RangeFilter:
    """Rejeicao de invalidos -> mediana (mata outlier) -> EMA (suaviza)."""

    def __init__(self, alpha=0.3, n=5):
        self.buf = deque(maxlen=n)
        self.alpha = alpha
        self.y = None

    def update(self, d):
        if d is None or not (DIST_MIN < d < DIST_MAX):
            return self.y          # amostra invalida: segura o ultimo valor
        self.buf.append(d)
        m = median(self.buf)
        if self.y is None:
            self.y = m
        else:
            self.y = self.alpha * m + (1 - self.alpha) * self.y
        return self.y


def is_valid(d):
    return d is not None and DIST_MIN < d < DIST_MAX

filter_front = RangeFilter(alpha=0.5, n=3)   # rapido: sensor de seguranca
filter_right = RangeFilter(alpha=0.3, n=5)   # suave: parede muda devagar

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyUSB0")
except Exception:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()

print("Entering loop. Ctrl+c to terminate")
time.sleep(3)

while not motor_serial.shutdown_now:
    iteration_start_time = time.time()
    
    raw_front = motor_serial.get_dist_1()
    raw_right = motor_serial.get_dist_2()

    dist_front = filter_front.update(raw_front)
    dist_right = filter_right.update(raw_right)

    # Ainda nao houve nenhuma leitura valida: fica parado em vez de estourar
    if dist_front is None or dist_right is None:
        print("Aguardando leitura valida... "
              f"(cru: front={raw_front}, right={raw_right})")
        motor_serial.send_command(0, 0)
        time.sleep(execution_period)
        continue

    print(f"front: {raw_front} -> {dist_front:6.1f} | "
          f"right: {raw_right} -> {dist_right:6.1f}")

    print(f'raw right sensor: {raw_right}')

    # Parada de emergencia: leitura crua tem zero lag, o filtro atrasa a reacao
    front_blocked = dist_front < front_threshold
    if EMERGENCY_ON_RAW and is_valid(raw_front) and raw_front < front_threshold:
        front_blocked = True

    if front_blocked:
        print('Obstacle ahead!')
        while dist_right > min_threshold:
            print('Obstacle ahead!')
            dist_right = filter_right.update(raw_right)
            print(dist_right)
            speed_motor_right = 50
            speed_motor_left = -50
            motor_serial.send_command(speed_motor_left, speed_motor_right)


    elif dist_right <= min_threshold:
        print('too close to the wall!')
        error = -1
        speed_motor_right = 50
        speed_motor_left = previous_output + kp*error

    elif min_threshold < dist_right <= median_threshold:
        print('correct distance!')
        error = 0
        speed_motor_right = 50
        speed_motor_left = 50

    elif median_threshold < dist_right < max_threshold:
        print('little deviation from the wall!')
        error = 1
        speed_motor_right = 50
        speed_motor_left = previous_output + kp*error

    elif dist_right >= max_threshold:
        error = 2
        print('big deviation from the wall! A turn, maybe?')
        speed_motor_right = 50
        speed_motor_left = previous_output + kp*error

    print(f'sending commands of {speed_motor_left} and {speed_motor_right}\n')
    motor_serial.send_command(speed_motor_left, speed_motor_right)

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if iteration_duration < execution_period:
        time.sleep(execution_period - iteration_duration)

print("Goodbye")