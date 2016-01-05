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
        self.chunk = 512 # Use a multiple of 8
        self.buffersize= (4 * self.chunk)
        self.data_in = aa.PCM(aa.PCM_CAPTURE, aa.PCM_NORMAL, 'front:CARD=Set,DEV=0')
        self.data_in.setchannels(self.no_channels)
        self.data_in.setrate(self.sample_rate)
        self.data_in.setformat(aa.PCM_FORMAT_S16_LE)
        self.data_in.setperiodsize(self.chunk)
        self.buffer = np.zeros(self.buffersize)
        self.matrix = []
        self.logpower = []
        self.noise = []
        self.run_thread = False
        self.window = np.blackman(self.buffersize)

    def calculate_levels(self, data, chunk, sample_rate, remove_noise=False):
        # Apply FFT - real data so rfft used
        fourier = np.fft.rfft(np.multiply(data, self.window))
        # Remove last element in array to make it the same size as chunk
        fourier = np.delete(fourier, len(fourier) - 1)
        # Find amplitude
        power = np.log10(np.abs(fourier)) ** 2
        power2 = power[:]
        # Araange array into 8 rows for the 8 bars on LED matrix
        # power = np.reshape(power, (8, self.buffersize/ 16))
        # matrix = np.int_(np.mean(power, axis=1))
        # Try logarithmic binning here
        self.logpower = []
        start = 2
        for i in [x ** 4 for x in range(1, 7)]:
            # print(i, start, start+i)
            self.logpower.append(np.int_(np.amax(power2[start:start + i])))
            start = start+i
        self.matrix = self.logpower

        #if remove_noise:
        #    self.matrix = np.clip([ (a-b) for a,b in zip(matrix, self.noise)],0,500)
        #else:
        #    self.matrix = matrix

    def findnoise(self):
        l,data = self.data_in.read()
        while not l:
            l, data = self.data_in.read()
        self.calculate_levels(data, self.chunk, self.sample_rate, False)
        self.noise = self.matrix[:]

    def read_data(self):
        # Read data from device
        l,data = self.data_in.read()
        # Convert raw data to numpy array
        data = unpack("%dh"%(len(data)/2),data)
        data = np.array(data, dtype='h')
        # shift buffer, append to end
        self.buffer = np.append(self.buffer[self.chunk:], data)
        if len(self.buffer) != self.buffersize:
            # print(len(self.buffer))
            self.read_data()
        else:
            return l
        
    def intensity(self, scale, power_max):
        power = self.matrix[:]
        power = [int(p**2) for p in power]
        if len(power) != len(power_max):
            power_max = [0]*len(power)
        power_max = [max(a, b) for a,b in zip(power, power_max)]
        #intensity = [int(p**2/10) for p in power]
        intensity = [a/(b/100) for a,b in zip(power, power_max)]
        intensity = [int(i*scale) for i in intensity]
        return intensity, power_max

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
        self.run_thread = True
        thread = Thread(target=self.analyse)
        thread.start()
        print("FFT Thread started.")

    def stop_analyse_thread(self):
        self.run_thread = False
