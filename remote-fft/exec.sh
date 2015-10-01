#!/bin/sh
arecord -Dplughw:1,0 | ./snd_fft - 192.168.178.37 5555
