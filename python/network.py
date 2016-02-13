import socket
import binascii
from threading import Thread
from time import sleep

class Net:

    pwm_resolution = 4095
    color_correction = [1, 0.70, 0.25]
    #color_correction = [1, 1, 1]
    gamma = 2.8

    ip = None
    port = None

    debug = False

    sck = None



    def __init__(self, ip, port, debug=False):
        self.ip = ip
        self.port = port
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.debug = debug

        self.run_thread = False

        self.delay = 0.03
        self.generator = None

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
        self.delay = delay
        if not self.generator:
            print("Set generator first.")
            return
        self.run_thread = True
        thread = Thread(target=self.iterate)
        thread.start()
        print("Network Thread started.")

    def stop_sender_thread(self):
        self.run_thread = False
