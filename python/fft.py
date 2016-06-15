import alsaaudio as aa
from struct import unpack
from threading import Thread
from time import sleep

import numpy as np


class FFT:
    def __init__(self, alsacard):
        """Set up audio."""
        self.sample_rate = 44100
        self.no_channels = 1
        self.chunk = 512  # Use a multiple of 8
        self.buffersize = (4 * self.chunk)
        self.data_in = aa.PCM(aa.PCM_CAPTURE, aa.PCM_NORMAL, alsacard)
        self.data_in.setchannels(self.no_channels)
        self.data_in.setrate(self.sample_rate)
        self.data_in.setformat(aa.PCM_FORMAT_S16_LE)
        self.data_in.setperiodsize(self.chunk)
        self.buffer = np.zeros(self.buffersize)
        self.matrix = []
        self.logpower = []
        self.power_max = []
        self.power_min = []
        self.noise = []
        self.run_thread = False
        self.window = np.blackman(self.buffersize)
        self.fourier = []
        self.thread = False

    @classmethod
    def available_pcms(cls):
        return aa.pcms()

    def calculate_levels(self, data, chunk, sample_rate, remove_noise=False):
        # Apply FFT - real data so rfft used
        self.fourier = np.fft.rfft(np.multiply(data, self.window))
        # Remove last element in array to make it the same size as chunk
        self.fourier = np.delete(self.fourier, len(self.fourier) - 1)
        # Find amplitude
        power = np.log10(np.abs(self.fourier)) ** 2
        power2 = power[:]
        # Araange array into 8 rows for the 8 bars on LED matrix
        # power = np.reshape(power, (8, self.buffersize/ 16))
        # matrix = np.int_(np.mean(power, axis=1))
        # Try logarithmic binning here
        self.logpower = []
        start = 2
        for i in range(1, 40):
            # print(i, start, start+i)
            self.logpower.append(np.int_(np.amax(power2[start:start + i])))
            start = start + i
        self.matrix = self.logpower

        # if remove_noise:
        #    self.matrix = np.clip([ (a-b) for a,b in zip(matrix, self.noise)],0,500)
        # else:
        #    self.matrix = matrix

    def findnoise(self):
        l, data = self.data_in.read()
        while not l:
            l, data = self.data_in.read()
        self.calculate_levels(data, self.chunk, self.sample_rate, False)
        self.noise = self.matrix[:]

    def read_data(self):
        # Read data from device
        l, data = self.data_in.read()
        # Convert raw data to numpy array
        data = unpack("%dh" % (len(data) / 2), data)
        data = np.array(data, dtype='h')
        # shift buffer, append to end
        self.buffer = np.append(self.buffer[self.chunk:], data)
        if len(self.buffer) != self.buffersize:
            # print(len(self.buffer))
            return self.read_data()
        else:
            return l

    def intensity(self, max_val=100):
        power = self.matrix[:]
        power = [int(p ** 2) for p in power]
        if len(power) != len(self.power_max):
            self.power_max = [0] * len(power)
        if len(power) != len(self.power_min):
            self.power_min = [0] * len(power)

        self.power_max = [max(a, b) for a, b in zip(power, self.power_max)]
        self.power_min = [min(a, b) for a, b in zip(power, self.power_min)]
        # Scaling attempts
        #
        # Okay:
        # intensity = [int(p**2/10) for p in power]
        #
        # Good with low power
        # intensity = [a/(b/100) for a,b in zip(power, self.power_max)]
        #
        # Min and Max scaling:
        intensity = [((max_val * (power[i] - self.power_min[i])) // (self.power_max[i] - self.power_min[i])) for i in
                     range(len(power))]

        # Relax max_measure
        # self.power_max = [i * 0.9999999999 for i in self.power_max]

        return intensity

    def rescale(self):
        self.power_max = []
        self.power_min = []

    def analyse(self, output=False, run=False):
        while self.run_thread or run:
            l = self.read_data()
            # self.data_in.pause(1) # Pause capture whilst RPi processes data
            if l:
                self.calculate_levels(self.buffer, self.buffersize, self.sample_rate)
                if output:
                    print(self.matrix)
            sleep(0.001)
            # self.data_in.pause(0) # Resume capture

    def start_analyse_thread(self):
        if self.run_thread is True:
            return

        self.run_thread = True
        self.thread = Thread(target=self.analyse)
        self.thread.start()
        print("FFT Thread started.")

    def stop_analyse_thread(self):
        self.run_thread = False
        self.thread.join()
