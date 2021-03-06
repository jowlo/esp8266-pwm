import binascii
import socket
from threading import Thread
from time import sleep


class Net:
    def __init__(self, ip, port, debug=False):
        self.debug = debug

        self.ip = ip
        self.port = port
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.delay = 0.03
        self.generator = None

        self.state = None

        self.thread = None
        self.run_thread = False

        self.gamma = 2.8
        self.pwm_resolution = 4095

        # self.color_correction = [1, 0.70, 0.25]
        # self.color_correction = [.6, .6, .6]
        self.color_correction = [.9, .9, .7]
        # self.color_correction = [1, 1, 1]

    def gamma_correction(self, i):
        """Return Gamma-corrected PWM-value."""
        return ((i / self.pwm_resolution) ** self.gamma) * self.pwm_resolution + 0.5

    def rgb_to_pwm(self, color):
        """Translate RGB-Color to PWM values including color and gamma correction."""
        c = [color[2], color[0], color[1]]
        cor = [self.color_correction[2], self.color_correction[0], self.color_correction[1]]
        return [int(self.gamma_correction(a * b * self.pwm_resolution)) for a, b in zip(c, cor)]

    def send(self, state):
        """Send a state of colors to ESP."""
        self.state = state
        data = bytearray([0, 126])  # "\x00\x7e"
        for strip_color in state:
            strip_pwm = self.rgb_to_pwm(strip_color)
            for i in range(3):
                strip_pwm[i] = min(self.pwm_resolution, strip_pwm[i])
                data.extend([(strip_pwm[i] & 0xff00) >> 8, strip_pwm[i] & 0x00ff])
        if self.debug:
            print(binascii.hexlify(data))
        self.sck.sendto(data, (self.ip, self.port))

    def iterate(self, output=False, run=False):
        while self.run_thread or run:
            self.send(next(self.generator))
            sleep(self.delay)

    def start_sender_thread(self, delay=0.03):
        if self.thread is not None:
            self.stop_sender_thread()
        self.delay = delay
        if not self.generator:
            print("Set generator first.")
            return
        self.run_thread = True
        self.thread = Thread(target=self.iterate)
        self.thread.start()
        print("Network Thread started.")

    def stop_sender_thread(self):
        self.run_thread = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None
