import socket
import binascii

class Net:
    
    pwm_resolution = 4095
    color_correction = [1, 0.70, 0.25]
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

    def gamma_correction(self, i):
        """Return Gamma-corrected PWM-value."""
        return ((i / self.pwm_resolution) ** self.gamma) * self.pwm_resolution + 0.5

    def rgb_to_pwm(self, color):
        """Translate RGB-Color to PWM values including color and gamma correction."""
        c = [color[1], color[0], color[2]]
        cor = [self.color_correction[1], self.color_correction[0], self.color_correction[2]]
        return [int(self.gamma_correction(a * b * self.pwm_resolution)) for a, b in zip(c, cor)]
    
    def send(self, state):
        """Send a state of colors to ESP."""
        data = bytearray([0, 126])  # "\x00\x7e"
        for strip_color in state:
            strip_pwm = self.rgb_to_pwm(strip_color)
            for i in range(3):
                data.extend([(strip_pwm[i] & 0xff00) >> 8, strip_pwm[i] & 0x00ff])
        if self.debug:
            print(binascii.hexlify(data))
        self.sck.sendto(data, (self.ip, self.port))    
