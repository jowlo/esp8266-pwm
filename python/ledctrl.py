import socket
import binascii
import math
import time

UDP_IP = "192.168.178.39"
UDP_PORT = 5555
STRIPS = 10

pwm_resolution = 4095
color_correction = [1, 0.70, 0.25]
#color_correction = [1, 1, 1]
gamma = 2.8
GROUPS = [[1], [2, 3], [4, 5, 6], [7, 8], [9]]


white = [1, 1, 1]
red = [1, 0, 0]
green = [0, 1, 0]
blue = [0, 0, 1]


def setup():
    """Return Socket with default configuration."""
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def gamma_correction(i):
    """Return Gamma-corrected PWM-value."""
    return ((i / pwm_resolution) ** gamma) * pwm_resolution + 0.5


def send_state(state, socket, port=UDP_PORT, addr=UDP_IP):
    """Send a state of colors to ESP."""
    data = bytearray([0, 126])  # "\x00\x7e"
    for strip_color in state:
        strip_pwm = rgb_to_pwm(strip_color)
        for i in range(3):
            data.extend([(strip_pwm[i] & 0xff00) >> 8, strip_pwm[i] & 0x00ff])
    print(binascii.hexlify(data))
    socket.sendto(data, (addr, port))


def rgb_to_pwm(color):
    """Translate RGB-Color to PWM values including color and gamma correction."""
    c = [color[1], color[0], color[2]]
    cor = [color_correction[1], color_correction[0], color_correction[2]]
    return [int(gamma_correction(a * b * pwm_resolution)) for a, b in zip(c, cor)]


def full_color(color):
    """Send a color to all strips."""
    send_state(full_color_state(color), setup())


def full_color_state(color):
    """Return a state with all strips set to color."""
    return [color for i in range(STRIPS)]


def rainbow_colors(num=2000, freq=.03):
    """Return list of rainbow colors with num elements"""
    colors = []
    for i in range(2000):
        colors.append([math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(0, 6, 2)])
    return colors


def rainbow_full_state(state, i, freq=.03):
    """Return a state with all strips in single color of rainbow, i is used as counter."""
    return full_color_state([math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(0, 6, 2)])


def rainbow_full():
    """Directly display rainbow fade with all strips in single color."""
    colors = rainbow_colors()
    for color in colors:
        send_state(full_color_state(color), setup())
        time.sleep(.03)


def state_off():
    """Return a state in which all strips are off."""
    return [[0, 0, 0] for i in range(STRIPS)]


def rainbow_moving(groups=GROUPS, freq=0.5):
    """Display rainbow colors using strip-groups, colors are moved."""
    colors = rainbow_colors(2000, freq)
    for i in range(len(colors)):
        state = state_off()
        for g in range(len(groups)):
            state = set_strips(state, groups[g], colors[i + g])
        send_state(state, setup())
        time.sleep(.03)


def rainbow_moving_state(state, i, groups=GROUPS, freq=0.5):
    """
    Return a state of rainbow colors moving through strip groups.

    i is used as counter.

    """
    colors = rainbow_colors(2000, freq)
    for g in range(len(groups)):
        state = set_strips(state, groups[g], colors[i + g])
    return state


def sine_map_state(state, i, groups=GROUPS, freq=0.5):
    """Use a sine-function to set the brightness of strip groups of a given state, cycles with i."""
    a_map = [math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(len(groups))]
    for g in range(len(groups)):
        state = set_strips(state, groups[g], [a_map[g] * c for c in state[groups[g][0]]])
    return state


def set_strips(state, strips, color):
    """Return a state in which given strips are set to color."""
    for i in strips:
        state[i] = color
    return state


def alpha(color, alpha):
    """Return a color with set alpha."""
    return [alpha * c for c in color]


def move_color_state(color, groups=GROUPS):
    """Yield states with one color moving through strips."""
    i = 0;
    while True:
        i = i + 1
        yield set_strips(state_off(), groups[i % len(groups)], color)



def alpha_state(state, i, freq=0.3):
    """Return a state in which all strips brightness is set, cycling with i."""
    for s in range(STRIPS):
        state = set_strips(state, [s], alpha(state[s], math.sin(freq * i) * 0.5 + 0.5))
        print(state)
    return state


def alpha_pulse_colors(color, freq=0.5):
    """Return a list colors where color is the base and alpha is cycled."""
    colors = []
    for i in range(2000):
        colors.append([(math.sin(freq * i) * 0.5 + 0.5) * c for c in color])
    return colors


def pulse_color(color, freq=0.5):
    """Display alpha-pulsing color."""
    colors = alpha_pulse_colors(color, freq)
    for color in colors:
        full_color(color)
        time.sleep(.03)


def led_funct(base, steps, *functions):
    """
    Yield steps-many states based on base, applying functions.

    The supplied functions have to take a state and a counter variable as
    parameters.  Functions are applied in given order.

    """
    for i in range(steps):
        state = base[:]
        for f in functions:
            state = f(state, i)
        yield state


def iterate_states(states, delay=0.03):
    """Display list of states one after the other."""
    for state in states:
        print(state)
        send_state(state, setup())
        time.sleep(delay)


def numbering():
    """Cycle through strips to find out numbering."""
    for i in range(STRIPS):
        state = state_off()
        print(i)
        send_state(set_strips(state, [i], [1, 1, 1]), setup())
        time.sleep(1)

"""
iterate_states(led_funct(state_off(), 100, rainbow_moving_state, alpha_state))
iterate_states(led_funct(full_color_state(white), 100, sine_map_state))
iterate_states(move_color_state(white), 0.1)
"""
