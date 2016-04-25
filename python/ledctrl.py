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

# UDP_IP = "192.168.4.1"
# UDP_PORT = 5555
# N = Net(UDP_IP, UDP_PORT)

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--fftdevice:", help="Do not start FFT-Thread (No Audio Input).",
                           action="store_true")
    args = argparser.parse_args()

    if args.fftdevice:
        # FFT_INST = FFT('front:CARD=Set,DEV=0')
        FFT_INST = FFT('front:CARD=CODEC,DEV=0')


class LED_Controller:
    def __init__(self, strips, udp_address, udp_port):
        self.strips = strips
        self.network = Net(udp_address, udp_port)
        self.fft = None
        self.state_factory = State(strips)
        self.color = Color()
        self.groups = [[a] for a in list(range(strips))]

    def full_color(self, color):
        """Send a color to all strips."""
        self.network.send(self.state_factory.full_color(color))

    def rainbow_full_state(self, state, i, freq=.03):
        """Return a state with all strips in single color of rainbow, i is used as counter."""
        return self.full_color([math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(0, 6, 2)])

    def rainbow_full(self):
        """Directly display rainbow fade with all strips in single color."""
        colors = Color.rainbow_colors()
        for color in colors:
            self.network.send(self.state_factory.full_color(color))
            time.sleep(.03)

    def rainbow_moving(self, groups=None, freq=0.5):
        if groups is None:
            groups = self.groups
        """Display rainbow colors using strip-groups, colors are moved."""
        colors = Color.rainbow_colors(2000, freq)
        for i in range(len(colors)):
            state = self.state_factory.state_off()
            for g in range(len(groups)):
                state = self.state_factory.set_strips(state, groups[g], colors[i + g])
            self.network.send(state)
            time.sleep(.03)

    def rainbow_moving_state(self, groups=None, freq=0.5):
        if groups is None:
            groups = self.groups
        """
        Return a state of rainbow colors moving through strip groups.

        i is used as counter.

        """
        colors = Color.rainbow_colors(2000, freq)
        i = 0
        state = self.state_factory.state_off()
        while True:
            i = (i + 1) % (len(colors) - len(groups))
            for g in range(len(groups)):
                state = self.state_factory.set_strips(state, groups[g], colors[i + g])
            yield state

    def sine_map_state(self, state, i, groups=GROUPS, freq=0.5):
        """Use a sine-function to set the brightness of strip groups of a given state, cycles with i."""
        a_map = [math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(len(groups))]
        for g in range(len(groups)):
            state = self.state_factory.set_strips(state, groups[g], [a_map[g] * c for c in state[groups[g][0]]])
        return state

    def move_color_state(self, color, groups=GROUPS, base=None):
        if base is None:
            base=self.state_factory.state_off()
        """Yield states with one color moving through strips."""
        i = 0;
        while True:
            i = (i + 1) % len(groups)
            yield self.state_factory.set_strips(base, groups[i], color)

    def alpha_state(self, state, i, freq=0.3):
        """Return a state in which all strips brightness is set, cycling with i."""
        for s in range(self.strips):
            state = self.state_factory.set_strips(state, [s], Color.alpha(state[s], math.sin(freq * i) * 0.5 + 0.5))
            if DEBUG:
                print(state)
        return state

    def alpha_pulse_colors(self, color, freq=0.5):
        """Return a list colors where color is the base and alpha is cycled."""
        colors = []
        for i in range(2000):
            colors.append([(math.sin(freq * i) * 0.5 + 0.5) * c for c in color])
        return colors

    def pulse_color(self, color, freq=0.5):
        """Display alpha-pulsing color."""
        colors = self.alpha_pulse_colors(color, freq)
        for color in colors:
            self.full_color(color)
            time.sleep(.03)

    def led_funct(self, base, steps, *functions):
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


    def iterate_states(self, states, delay=0.03):
        """Display list of states one after the other."""
        for state in states:
            if DEBUG:
                print(state)
            self.network.send(state)
            time.sleep(delay)

    def iterate_states_threaded(self, generator, delay=0.03):
        self.network.generator = generator
        if not self.network.run_thread:
            self.network.start_sender_thread()

    def iterate_generator(self, generator):
        self.network.generator = generator

    def numbering(self):
        """Cycle through strips to find out numbering."""
        for i in range(self.strips):
            state = self.state_factory.state_off()
            print(i)
            self.network.send(self.state_factory.set_strips(state, [i], [1, 1, 1]))
            time.sleep(1)

    def fft_init(self, delay=0.03):
        """
        Initialize a thread that starts FFT-Analysation.

        If a thread has already been started and FFT is running, no
        new thread is started.
        """
        if not self.fft.run_thread:
            self.fft.start_analyse_thread()
        time.sleep(delay)

    def fft_destroy(self):
        """Stop FFT-thread."""
        self.fft.stop_analyse_thread()

    def fft_eq(self, colors=None, scale=1, delay=0.03, threshold=0, groups=GROUPS):
        if colors is None:
            colors = self.color.heat_colors()
        self.fft_init()
        state = self.state_factory.state_off()
        while True:
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            for i in range(len(groups)):
                if i < len(intensity):
                    self.state_factory.set_strips(state, GROUPS[i], colors[np.clip(intensity[i], 0, 99)])
            yield state

    def fft_pulse_map(self, colors=None, scale=1, delay=0.03, threshold=0, channel=0):
        if colors is None:
            colors = self.color.heat_colors()
        self.fft_init()
        state = self.state_factory.state_off()
        while True:
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            state = self.state_factory.full_color(colors[np.clip(intensity[channel], 0, len(colors) - 1)])
            yield state

    def fft_pulse_color(self, color=Color.white, scale=1, delay=0.03, channel=0, threshold=0):
        self.fft_init()
        state = self.state_factory.state_off()
        while True:
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            state = self.state_factory.full_color(Color.alpha(color, intensity[channel] / 100))
            yield state

    def fft_pulse_cycle(self, cycle_colors=None, scale=1, delay=0.03, threshold=0, channel=0):
        if cycle_colors is None:
            cycle_colors = self.color.rainbow_colors()
        self.fft_init()
        cycle = 1
        state = self.state_factory.state_off()
        while True:
            cycle = (cycle + 1) % len(cycle_colors)
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            state = self.state_factory.full_color(Color.alpha(cycle_colors[cycle], intensity[channel] / 100))
            yield state

    def fft_move_color(self, color=None, groups=GROUPS, channel=0, decay=0.8, scale=1, delay=0.03, threshold=0):
        self.fft_init()
        state = self.state_factory.state_off()
        while True:
            c = color()
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            nextstate = self.state_factory.state_off()
            for i in range(1, len(groups)):
                self.state_factory.set_strips(nextstate, groups[i], self.color.alpha(state[groups[i - 1][0]], decay))
            self.state_factory.set_strips(nextstate, groups[0], self.color.alpha(c, intensity[channel] / 100))
            state = nextstate[:]
            yield state

    def fft_move_map(self, colors=None, groups=GROUPS, channel=0, scale=1, delay=0.03, decay=1, threshold=0):
        if colors is None:
            colors = self.color.heat_colors()
        self.fft_init()
        state = self.state_factory.state_off()
        while True:
            intensity = [((scale * i) if i > threshold else 0) for i in self.fft.intensity()]
            if DEBUG:
                print(intensity)
            nextstate = self.state_factory.state_off()
            for i in range(1, len(groups)):
                self.state_factory.set_strips(nextstate, groups[i], self.color.alpha(state[groups[i - 1][0]], decay))
            self.state_factory.set_strips(nextstate, groups[0], colors[int(np.clip(intensity[channel], 0, 99))])
            state = nextstate[:]
            yield state

    def off(self):
        self.network.stop_sender_thread()
        self.network.send(self.state_factory.state_off())

    def stop_all_threads(self):
        self.network.stop_sender_thread()
        self.network.send(self.state_factory.state_off())
        if self.fft:
            self.fft.stop_analyse_thread()

    def testrgb(self, delay):
        for c in [Color.red, Color.green, Color.blue, Color.white]:
            self.full_color(c)
            time.sleep(delay)

