import alsaaudio as aa
from threading import Thread
from time import sleep
from struct import unpack
import numpy as np

class FFT:
    def __init__(self):
        """Set up audio."""
        self.sample_rate = 44100
        self.no_channels = 1
        self.chunk = 2048 # Use a multiple of 8
        self.buffer = 4*self.chunk
        self.data_in = aa.PCM(aa.PCM_CAPTURE, aa.PCM_NORMAL, 'front:CARD=Set,DEV=0')
        self.data_in.setchannels(self.no_channels)
        self.data_in.setrate(self.sample_rate)
        self.data_in.setformat(aa.PCM_FORMAT_S16_LE)
        self.data_in.setperiodsize(self.chunk)
        self.matrix = []
        self.logpower = []
        self.noise = []
        self.run_thread = False

    def calculate_levels(self, data, chunk, sample_rate, remove_noise=True):
        # Convert raw data to numpy array
        data = unpack("%dh"%(len(data)/2),data)
        data = np.array(data, dtype='h')
        # Apply FFT - real data so rfft used
        fourier = np.fft.rfft(data)
        # Remove last element in array to make it the same size as chunk
        fourier = np.delete(fourier, len(fourier) - 1)
        # Find amplitude
        power = np.log10(np.abs(fourier)) ** 2
        power2 = power[:]
        # Araange array into 8 rows for the 8 bars on LED matrix
        power = np.reshape(power, (8, self.chunk / 16))
        matrix = np.int_(np.mean(power, axis=1))
        # Try logarithmic binning here
        start = 1
        self.logpower = []
        for i in [x**2 for x in range(10)]:
            start += i
            self.logpower.append(np.int_(np.mean(power2[start:start+i])))
        print(self.logpower)

        if remove_noise:
            self.matrix = np.clip([ (a-b) for a,b in zip(matrix, self.noise)],0,500)
        else:
            self.matrix = matrix

    def findnoise(self):
        l,data = self.data_in.read()
        while not l:
            l, data = self.data_in.read()
        self.calculate_levels(data, self.chunk, self.sample_rate, False)
        self.noise = self.matrix[:]

    def analyse(self, output=False, run=False):
        while self.run_thread or run:
            # Read data from device
            l,data = self.data_in.read()
            # self.data_in.pause(1) # Pause capture whilst RPi processes data
            if l:
                self.calculate_levels(data, self.chunk, self.sample_rate)
                if output:
                    print(self.matrix)
            sleep(0.001)
            # self.data_in.pause(0) # Resume capture

    def start_analyse_thread(self):
        self.run_thread = True
        thread = Thread(target=self.analyse)
        thread.start()
        print("FFT Thread started.")

    def stop_analyse_thread(self):
        self.run_thread = False
