import math
import time
from fft import FFT
import numpy as np
from color import Color
from network import Net
from state_factory import State

DEBUG=False

STRIPS = 10
UDP_IP = "192.168.178.39"
UDP_PORT = 5555

GROUPS = [[1], [2, 3], [4, 5, 6], [7, 8], [9]]
FFT_INST = FFT()
N = Net(UDP_IP, UDP_PORT)
S = State(STRIPS)
Color = Color()



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


def rainbow_moving_state(state, i, groups=GROUPS, freq=0.5):
    """
    Return a state of rainbow colors moving through strip groups.

    i is used as counter.

    """
    colors = Color.rainbow_colors(2000, freq)
    for g in range(len(groups)):
        state = S.set_strips(state, groups[g], colors[i + g])
    return state


def sine_map_state(state, i, groups=GROUPS, freq=0.5):
    """Use a sine-function to set the brightness of strip groups of a given state, cycles with i."""
    a_map = [math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(len(groups))]
    for g in range(len(groups)):
        state = S.set_strips(state, groups[g], [a_map[g] * c for c in state[groups[g][0]]])
    return state


def move_color_state(color, groups=GROUPS):
    """Yield states with one color moving through strips."""
    i = 0;
    while True:
        i = i + 1
        yield S.set_strips(S.state_off(), groups[i % len(groups)], color)



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


def numbering():
    """Cycle through strips to find out numbering."""
    for i in range(STRIPS):
        state = S.state_off()
        if DEBUG: 
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
    
    
def fft_eq(colors=Color.heat_colors(), scale=1, delay=0.03):
    fft_init()
    power_max = []
    state = S.state_off()
    while True:
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)        
        for i in range(len(GROUPS)):
            if i < len(intensity):
                S.set_strips(state, GROUPS[i], colors[np.clip(intensity[i], 0, 99)])
        N.send(state)
        time.sleep(delay)
                        
                        
def fft_pulse_map(colors=Color.heat_colors(), scale=1, delay=0.03, channel=0):
    fft_init()
    power_max = []
    state = S.state_off()
    while True:
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)
        state = S.full_color(colors[np.clip(intensity[channel], 0, len(colors)-1)])
        N.send(state)
        time.sleep(delay)
        
        
def fft_pulse_color(color=Color.white, scale=1, delay=0.03, channel=0):
    fft_init()
    power_max = []
    state = S.state_off()
    while True:
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)
        state = S.full_color(Color.alpha(color, intensity[channel]/100))
        N.send(state)
        time.sleep(delay)
        
        
def fft_pulse_cycle(cycle_colors=Color.rainbow_colors(), scale=1, delay=0.03, channel=0):
    fft_init()
    power_max = []
    cycle = 1
    state = S.state_off()
    while True:        
        cycle = (cycle + 1) % len(cycle_colors)
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)
        state = S.full_color(Color.alpha(cycle_colors[cycle], intensity[channel]/100))
        N.send(state)
        time.sleep(delay)
        

def fft_move_color(color=Color.white, groups=GROUPS, channel=0, decay=0.8, scale=1, delay=0.03):
    fft_init()
    power_max = []
    state = S.state_off()
    while True:
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)        
        nextstate = S.state_off()
        for i in range(1,len(groups)):
            S.set_strips(nextstate, groups[i], Color.alpha(state[groups[i-1][0]], decay))
        S.set_strips(nextstate, groups[0], Color.alpha(color, intensity[channel]/100))
        state = nextstate[:]        
        N.send(state)
        time.sleep(delay)
        
def fft_move_map(colors=Color.heat_colors(), groups=GROUPS, channel=0, scale=1, delay=0.03, decay=1):
    fft_init()
    power_max = []
    state = S.state_off()
    while True:
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)    
        nextstate = S.state_off()
        for i in range(1,len(groups)):
            S.set_strips(nextstate, groups[i], Color.alpha(state[groups[i-1][0]], decay))
        S.set_strips(nextstate, groups[0], colors[np.clip(intensity[channel], 0, 99)])
        state = nextstate[:]
        N.send(state)
        time.sleep(delay)
    

def fft_test(mode='EQ', color=Color.white, channel=0, scale=1, delay=0.03, decay=0.8, groups=GROUPS):
    """ Deprecated. Use Individual Functions."""
    fft_init()
    power_max = []
    cycle = 1
    state = S.state_off()
    heat_colors = Color.heat_colors()
    rainbow_colors = Color.rainbow_colors(num=100)

    while True:
        cycle = (cycle + 1)%100
        intensity, power_max = FFT_INST.intensity(scale, power_max)
        if DEBUG:
            print(power_max, intensity)
        if mode is 'EQ':
            for i in range(len(GROUPS)):
                if i < len(intensity):
                    S.set_strips(state, GROUPS[i], heat_colors[np.clip(intensity[i], 0, 99)])
        elif mode is 'PULSE_HEAT':
            state = S.full_color(heat_colors[np.clip(intensity[channel], 0, 99)])
        elif mode is 'PULSE_COLOR':
            state = S.full_color(Color.alpha(color, intensity[channel]/100))
        elif mode is 'PULSE_RAINBOW':
            state = S.full_color(Color.alpha(rainbow_colors[cycle], intensity[channel]/100))
        elif mode is 'MOVE_BIT_COLOR':
            state.insert(0, Color.alpha(color, intensity[channel]/100))
            state.pop()
            print(state)
        elif mode is 'MOVE_BIT_DECAY':
            nextstate = S.state_off()
            for i in range(1,len(groups)):
                S.set_strips(nextstate, groups[i], Color.alpha(state[groups[i-1][0]], decay))
            S.set_strips(nextstate, groups[0], Color.alpha(color, intensity[channel]/100))
            state = nextstate[:]
        elif mode is 'MOVE_BIT_HEAT':
            nextstate = S.state_off()
            for i in range(1,len(groups)):
                S.set_strips(nextstate, groups[i], state[groups[i-1][0]])
            S.set_strips(nextstate, groups[0], heat_colors[np.clip(intensity[channel], 0, 99)])
            state = nextstate[:]

        N.send(state)
        time.sleep(delay)


"""
iterate_states(led_funct(S.state_off(), 100, rainbow_moving_state, alpha_state))
iterate_states(led_funct(S.full_color(Color.white), 100, sine_map_state))
iterate_states(move_color_state(Color.white), 0.1)
"""
