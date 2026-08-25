import imrt_robot_serial
import time
import sys
from collections import deque
from statistics import median

# ---------------------------------------------------------------- controle
kp = 2.0
ti = 3.0                      # segundos (nao 100!)
ki = kp / ti

min_threshold = 10.0          # perto demais da parede
median_threshold = 20.0       # limite superior da faixa boa
max_threshold = 50.0          # acima disso: parede sumiu
front_threshold = 5.0         # frente bloqueada

setpoint = (min_threshold + median_threshold) / 2.0   # 15 cm
base_speed = 25.0
u_min, u_max = -100.0, 100.0
error_clamp = 20.0            # limita o erro em aberturas

execution_frequency = 10
execution_period = 1. / execution_frequency

# ---------------------------------------------------------------- sensores
DIST_MIN = 1.0
DIST_MAX = 255.0
EMERGENCY_ON_RAW = True       # parada de emergencia usa leitura crua (sem lag)

# ---------------------------------------------------------------- manobras
# CALIBRAR NO ROBO, com a bateria no nivel que sera usado na prova
T_90 = 0.90                   # s para girar 90 graus a +-50
T_ADVANCE = 0.80              # s para o eixo passar a quina
T_REACQ_MAX = 2.0             # desiste de reencontrar a parede depois disso

RIGHT_OPEN = max_threshold - 5.0   # 45: parede sumiu
RIGHT_SEEN = max_threshold - 15.0  # 35: parede reencontrada (histerese)
OPEN_CONFIRM = 3                   # ciclos consecutivos para confirmar
FRONT_CLEAR = 2.5 * front_threshold


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

# ---------------------------------------------------------------- estado
state = "FOLLOW"
t_state = time.time()
open_count = 0
int_error = 0.0


def set_state(s):
    """Troca de estado zerando o integrador (a manobra invalida o historico)."""
    global state, t_state, int_error
    state = s
    t_state = time.time()
    int_error = 0.0
    print(f">>> {s}")


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

    # Parada de emergencia: leitura crua tem zero lag, o filtro atrasa a reacao
    front_blocked = dist_front < front_threshold
    if EMERGENCY_ON_RAW and is_valid(raw_front) and raw_front < front_threshold:
        front_blocked = True

    elapsed = time.time() - t_state
    speed_motor_left = 0.0
    speed_motor_right = 0.0

    # ------------------------------------------------------------ FOLLOW
    if state == "FOLLOW":
        open_count = open_count + 1 if dist_right > RIGHT_OPEN else 0

        if open_count >= OPEN_CONFIRM:
            print('parede sumiu a direita!')
            # frente ja bloqueada: nao da pra avancar, gira em cima da quina
            set_state("ROTATE_RIGHT" if front_blocked else "ADVANCE")
            open_count = 0
            continue

        if front_blocked:
            print('Obstacle ahead!')
            set_state("ROTATE_LEFT")
            continue

        # diagnostico nas faixas antigas (nao controla mais nada)
        if dist_right <= min_threshold:
            print('too close to the wall!')
        elif dist_right <= median_threshold:
            print('correct distance!')
        elif dist_right < max_threshold:
            print('little deviation from the wall!')
        else:
            print('big deviation from the wall!')

        # PI posicional com erro continuo + anti-windup por clamping
        error = dist_right - setpoint
        error = max(-error_clamp, min(error_clamp, error))

        u = base_speed + kp * error + ki * int_error
        u_sat = max(u_min, min(u_max, u))
        if u == u_sat:
            int_error += error * execution_period

        speed_motor_left = u_sat
        speed_motor_right = base_speed

    # ------------------------------------------------------------ ADVANCE
    elif state == "ADVANCE":
        # anda reto para o eixo do robo passar a quina antes de girar
        speed_motor_left = base_speed
        speed_motor_right = base_speed
        if front_blocked or elapsed > T_ADVANCE:
            set_state("ROTATE_RIGHT")
            continue

    # ------------------------------------------------------- ROTATE_RIGHT
    elif state == "ROTATE_RIGHT":
        speed_motor_left = 50
        speed_motor_right = -50
        if elapsed > T_90:
            set_state("REACQUIRE")
            continue

    # -------------------------------------------------------- ROTATE_LEFT
    elif state == "ROTATE_LEFT":
        speed_motor_left = -50
        speed_motor_right = 50
        if elapsed > T_90:
            # volta para FOLLOW: se ainda estiver bloqueado, gira de novo.
            # Dois giros seguidos = o 180 do beco sem saida, de graca.
            set_state("FOLLOW")
            continue

    # ---------------------------------------------------------- REACQUIRE
    elif state == "REACQUIRE":
        # anda reto ate reencontrar a parede no corredor novo
        speed_motor_left = base_speed
        speed_motor_right = base_speed
        if dist_right < RIGHT_SEEN or front_blocked or elapsed > T_REACQ_MAX:
            set_state("FOLLOW")
            continue

    print(f"[{state}] front: {raw_front} -> {dist_front:6.1f} | "
          f"right: {raw_right} -> {dist_right:6.1f} | "
          f"cmd: {speed_motor_left:6.1f} {speed_motor_right:6.1f}")

    motor_serial.send_command(speed_motor_left, speed_motor_right)

    iteration_end_time = time.time()
    iteration_duration = iteration_end_time - iteration_start_time
    if iteration_duration < execution_period:
        time.sleep(execution_period - iteration_duration)

motor_serial.send_command(0, 0)
print("Goodbye")