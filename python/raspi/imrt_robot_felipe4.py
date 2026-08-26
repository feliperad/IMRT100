import imrt_robot_serial
import time
import sys
from collections import deque
from statistics import median

# ---------------------------------------------------------------- controle
kp = 2.0
ti = 300
td = 0.0                      # deixe em 0 ate o robo andar reto; ver notas

setpoint = 20.0               # cm
base_speed = 65.0
u_min, u_max = -100.0, 100.0
error_min, error_max = -20.0, 20.0    # clamp assimetrico do erro

max_threshold = 150          # cm: acima disso a parede sumiu (nao usado ainda)
front_threshold = 12.0         # cm: frente bloqueada
front_clear = 45.0   # cm: frente livre de novo (histerese)

turn_speed = 80

execution_frequency = 10
execution_period = 1. / execution_frequency

# ---------------------------------------------------------------- sensores
# Limites em CENTIMETROS: o filtro trabalha em cm, nao em unidades cruas.
DIST_MIN = 2.0
DIST_MAX = 400.0
EMERGENCY_ON_RAW = True       # parada de emergencia usa leitura crua (sem lag)


def conversao_raw_cm(raw):
    """Converte a leitura crua para cm. Propaga None em vez de estourar."""
    if raw is None:
        return None
    return (raw + 1.2814)* (398.0/255.0)

def manobra(left, right, duracao):
    """Mantem o comando ativo por 'duracao' segundos, alimentando os filtros."""
    t0 = time.time()
    while not motor_serial.shutdown_now and (time.time() - t0) < duracao:
        t = time.time()
        filter_front.update(conversao_raw_cm(motor_serial.get_dist_1()))
        filter_right.update(conversao_raw_cm(motor_serial.get_dist_2()))
        motor_serial.send_command(int(left), int(right))
        dt = time.time() - t
        if dt < execution_period:
            time.sleep(execution_period - dt)


class RangeFilter:
    """Rejeicao de invalidos -> mediana (mata outlier) -> EMA (suaviza).

    Recebe e devolve CENTIMETROS.
    """

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


def acquire_signals():
    raw_front = conversao_raw_cm(motor_serial.get_dist_1())
    raw_right = conversao_raw_cm(motor_serial.get_dist_2())
    dist_front = filter_front.update(raw_front)
    dist_right = filter_right.update(raw_right)

    return dist_front, dist_right, raw_front


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

int_error = 0.0
previous_error = 0.0
rastrear_parede = True
uturn = False
front_blocked = False
open_count = 0

# ----------------------------------------------- início do loop
while not motor_serial.shutdown_now:
    iteration_start_time = time.time()

    dist_front, dist_right, _ = acquire_signals()

    # Ainda nao houve nenhuma leitura valida: fica parado em vez de estourar
    if dist_front is None or dist_right is None:
        print("Aguardando leitura valida... "
              f"(cm: front={dist_front}, right={dist_right})")
        motor_serial.send_command(0, 0)
        time.sleep(execution_period)
        continue

    #-----------------------------
    # estado 1 - curva à esquerda
    #-----------------------------
    if front_blocked:
        print('Obstacle ahead! Girando a esquerda...')
        int_error = 0.0
        previous_error = 0.0

        # while not motor_serial.shutdown_now:
        #     turn_start_time = time.time()

        #     dist_front, dist_right, _ = acquire_signals()
        #     motor_serial.send_command(-turn_speed, turn_speed)

        #     if dist_front > front_clear and dist_right < 1.2*setpoint:
        #         break

        #     turn_duration = time.time() - turn_start_time
        #     if turn_duration < execution_period:
        #         time.sleep(execution_period - turn_duration)

        manobra(-100,100, 1.7)

        motor_serial.send_command(0, 0)

        # transições
        print('going to state 0 - rastrear parede')
        rastrear_parede = True
        front_blocked = False
        uturn = False
    #-----------------------------

    #-----------------------------
    # estado 0: rastreando parede
    #-----------------------------
    if rastrear_parede:
        dist_front, dist_right, raw_front = acquire_signals()

        if dist_front <= front_threshold:
            print('going to state 1 - front blocked (left turn)')
            front_blocked = True
            uturn = False
            rastrear_parede = False

        if dist_right > max_threshold:
            open_count += 1
        else:
            open_count = 0

        if open_count >= 3 and dist_front > front_threshold:
            open_count = 0
            print('going to state 2 - right turn')
            front_blocked = False
            uturn = True
            rastrear_parede = False

        error = max(error_min, min(error_max, dist_right - setpoint))
        diff_error = (error - previous_error) / execution_period
        if diff_error > 150:
            setar = True

        print(f'estou no estado rastrear parede e diff error = {diff_error}')

        u = kp * (error + (1.0 / ti) * int_error + td * diff_error)
        u_sat = max(-2 * base_speed, min(2 * base_speed, u))

        if u == u_sat:
            int_error += error * execution_period

        previous_error = error

        left = base_speed + u_sat / 2.0
        right = base_speed - u_sat / 2.0

        # Se estourou o limite do motor, escala o par mantendo o diferencial
        peak = max(abs(left), abs(right))
        if peak > u_max:
            left *= u_max / peak
            right *= u_max / peak

        speed_motor_left, speed_motor_right = left, right

        print(f"front: {dist_front:6.1f} | right: {dist_right:6.1f} | "
            f"e={error:6.2f} i={int_error:7.2f} u={u_sat:7.2f} | "
            f"cmd: {speed_motor_left:6.1f} {speed_motor_right:6.1f}")

        motor_serial.send_command(int(speed_motor_left), int(speed_motor_right))
    #-----------------------------

    #---------------------------
    # estado 2: curva à direita
    #---------------------------
    if uturn:
        print('Curva à direita...')
        int_error = 0.0
        previous_error = 0.0

        manobra(base_speed,base_speed, 2.7)
        manobra(base_speed, -base_speed, 2.6)
        manobra(base_speed, base_speed, 6)

        dist_front, dist_right, _ = acquire_signals()

        if dist_right > 60:
            print('manobras adicionais')
            manobra(base_speed, -base_speed, 3.5)
            manobra(base_speed, base_speed, 6)

        print('going to state 0 - rastrear parede')
        rastrear_parede = True
        front_blocked = False
        uturn = False
                
    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if iteration_duration < execution_period:
        time.sleep(execution_period - iteration_duration)

motor_serial.send_command(0, 0)
print("Goodbye")