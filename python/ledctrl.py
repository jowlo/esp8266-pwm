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
# GROUPS = [[a] for a in list(range(0, 9))]
#GROUPS = [[0], [2], [3], [4], [5], [7], [8], [6], [9]]
GROUPS = [[0], [1], [3], [2], [4], [5], [6], [7], [8], [9]]

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


class LedController:
    def __init__(self, strips, udp_address, udp_port):
        self.strips = strips
        self.network = Net(udp_address, udp_port, debug=False)
        self.fft = None
        self.state_factory = State(strips)
        self.color = Color()
        # self.groups = [[a] for a in list(range(strips))]
        # self.groups = [[0], [2], [3], [4], [5], [7], [8], [6], [9]]
        self.groups = GROUPS

    def full_color(self, color):
        """Send a color to all strips."""
        self.network.send(self.state_factory.full_color(color))

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

    def numbering(self):
        """Cycle through strips to find out numbering."""
        for i in range(self.strips):
            state = self.state_factory.state_off()
            print(i)
            self.network.send(self.state_factory.set_strips(state, [i], [1, 1, 1]))
            time.sleep(1)

    def numbering_groups(self):
        for i in self.groups:
            state = self.state_factory.state_off()
            print(i)
            self.network.send(self.state_factory.set_strips(state, i, [1, 0, 0]))
            time.sleep(1)

