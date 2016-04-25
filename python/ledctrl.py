import argparse
import math
import time

import numpy as np

from color import Color
from fft import FFT
from network import Net
from state_factory import State

DEBUG = False

# GROUPS = [[1], [2, 3], [4, 5, 6], [7, 8], [9]]
GROUPS = [[a] for a in list(range(0, 9))]

g_center_out = [[4], [0, 8], [1, 7], [2, 6], [3, 5]]
g_front_to_back = [[0, 8], [1, 7], [2, 6], [3, 5]]
g_left_to_right = [[0], [1], [2], [3], [5], [6], [7], [8]]

UDP_IP = "192.168.4.1"
UDP_PORT = 5555
N = Net(UDP_IP, UDP_PORT)

STRIPS = 10
S = State(STRIPS)
Color = Color()
FFT_INST = None

def main():

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--fft-device:", help="Do not start FFT-Thread (No Audio Input).",
                           action="store_true")
    args = argparser.parse_args()

    if args.fft-device:
        # FFT_INST = FFT('front:CARD=Set,DEV=0')
        FFT_INST = FFT('front:CARD=CODEC,DEV=0')


def full_color(color):
    """Send a color to all strips."""
    N.send(S.full_color(color))


def rainbow_full_state(state, i, freq=.03):
    """Return a state with all strips in single color of rainbow, i is used as counter."""
    return S.full_color([math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(0, 6, 2)])


def rainbow_full():
    """Directly display rainbow fade with all strips in single color."""
    colors = Color.rainbow_colors()
    for color in colors:
        N.send(S.full_color(color))
        time.sleep(.03)


def rainbow_moving(groups=GROUPS, freq=0.5):
    """Display rainbow colors using strip-groups, colors are moved."""
    colors = Color.rainbow_colors(2000, freq)
    for i in range(len(colors)):
        state = S.state_off()
        for g in range(len(groups)):
            state = S.set_strips(state, groups[g], colors[i + g])
        N.send(state)
        time.sleep(.03)


def rainbow_moving_state(groups=GROUPS, freq=0.5):
    """
    Return a state of rainbow colors moving through strip groups.

    i is used as counter.

    """
    colors = Color.rainbow_colors(2000, freq)
    i = 0
    state = S.state_off()
    while True:
        i = (i + 1) % (len(colors) - len(groups))
        for g in range(len(groups)):
            state = S.set_strips(state, groups[g], colors[i + g])
        yield state


def sine_map_state(state, i, groups=GROUPS, freq=0.5):
    """Use a sine-function to set the brightness of strip groups of a given state, cycles with i."""
    a_map = [math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(len(groups))]
    for g in range(len(groups)):
        state = S.set_strips(state, groups[g], [a_map[g] * c for c in state[groups[g][0]]])
    return state


def move_color_state(color, groups=GROUPS, base=None):
    if base is None:
        base=S.state_off()
    """Yield states with one color moving through strips."""
    i = 0;
    while True:
        i = (i + 1) % len(groups)
        yield S.set_strips(base, groups[i], color)


def alpha_state(state, i, freq=0.3):
    """Return a state in which all strips brightness is set, cycling with i."""
    for s in range(STRIPS):
        state = S.set_strips(state, [s], Color.alpha(state[s], math.sin(freq * i) * 0.5 + 0.5))
        if DEBUG:
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
        if DEBUG:
            print(state)
        N.send(state)
        time.sleep(delay)


def iterate_states_threaded(generator, delay=0.03):
    N.generator = generator
    if not N.run_thread:
        N.start_sender_thread()


def iterate_generator(generator):
    N.generator = generator


def numbering():
    """Cycle through strips to find out numbering."""
    for i in range(STRIPS):
        state = S.state_off()
        print(i)
        N.send(S.set_strips(state, [i], [1, 1, 1]))
        time.sleep(1)


def fft_init(delay=0.03):
    """
    Initialize a thread that starts FFT-Analysation.

    If a thread has already been started and FFT is running, no
    new thread is started.
    """
    if not FFT_INST.run_thread:
        FFT_INST.start_analyse_thread()
    time.sleep(delay)


def fft_destroy():
    """Stop FFT-thread."""
    FFT_INST.stop_analyse_thread()


def fft_eq(colors=Color.heat_colors(), scale=1, delay=0.03, threshold=0, groups=GROUPS):
    fft_init()
    state = S.state_off()
    while True:
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        for i in range(len(groups)):
            if i < len(intensity):
                S.set_strips(state, GROUPS[i], colors[np.clip(intensity[i], 0, 99)])
        yield state


def fft_pulse_map(colors=Color.heat_colors(), scale=1, delay=0.03, threshold=0, channel=0):
    fft_init()
    state = S.state_off()
    while True:
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        state = S.full_color(colors[np.clip(intensity[channel], 0, len(colors) - 1)])
        yield state


def fft_pulse_color(color=Color.white, scale=1, delay=0.03, channel=0, threshold=0):
    fft_init()
    state = S.state_off()
    while True:
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        state = S.full_color(Color.alpha(color, intensity[channel] / 100))
        yield state


def fft_pulse_cycle(cycle_colors=Color.rainbow_colors(), scale=1, delay=0.03, threshold=0, channel=0):
    fft_init()
    cycle = 1
    state = S.state_off()
    while True:
        cycle = (cycle + 1) % len(cycle_colors)
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        state = S.full_color(Color.alpha(cycle_colors[cycle], intensity[channel] / 100))
        yield state


def fft_move_color(color=Color.white, groups=GROUPS, channel=0, decay=0.8, scale=1, delay=0.03, threshold=0):
    fft_init()
    state = S.state_off()
    while True:
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        nextstate = S.state_off()
        for i in range(1, len(groups)):
            S.set_strips(nextstate, groups[i], Color.alpha(state[groups[i - 1][0]], decay))
        S.set_strips(nextstate, groups[0], Color.alpha(color, intensity[channel] / 100))
        state = nextstate[:]
        yield state


def fft_move_map(colors=Color.heat_colors(), groups=GROUPS, channel=0, scale=1, delay=0.03, decay=1, threshold=0):
    fft_init()
    state = S.state_off()
    while True:
        intensity = [((scale * i) if i > threshold else 0) for i in FFT_INST.intensity()]
        if DEBUG:
            print(intensity)
        nextstate = S.state_off()
        for i in range(1, len(groups)):
            S.set_strips(nextstate, groups[i], Color.alpha(state[groups[i - 1][0]], decay))
        S.set_strips(nextstate, groups[0], colors[int(np.clip(intensity[channel], 0, 99))])
        state = nextstate[:]
        yield state


def off():
    N.stop_sender_thread()
    N.send(S.state_off())


def stop_all_threads():
    N.stop_sender_thread()
    N.send(S.state_off())
    FFT_INST.stop_analyse_thread()

def testrgb(delay):
    for c in [Color.red, Color.green, Color.blue, Color.white]:
        full_color(c)
        time.sleep(delay)


"""
iterate_states(led_funct(S.state_off(), 100, rainbow_moving_state, alpha_state))
iterate_states(led_funct(S.full_color(Color.white), 100, sine_map_state))
iterate_states(move_color_state(Color.white), 0.1)
"""
