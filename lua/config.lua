local modname = ...
local M = {}

_G[modname] = M

i2c_id = 0
i2c_sda = 3
i2c_scl = 4

pca9685_addr = {0x40, 0x45}
