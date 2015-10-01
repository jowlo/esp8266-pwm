-- udp listen port.
-- protocol is easy:
--      2 byte for cmd. first is not used, second is CMD
--      2 bytes per output, first byte is MSB. in order.
port = 5555

PWM_CMD = 126 -- 0x7e
PATTERN_CMD = 127 -- 0x7f

-- pins in ascending order of frequency ranges and total of pins.
pins = { 8, 4, 3, 2, 1 }
numout = 5

-- minimal duty cycle. zero for default off
min = 0

-- max duty cycle. above 1023 will err.
max = 1023

-- afterglow
glow = false
reduce = 20

dofile("handlers.lua")

-- gpio.mode(pin,gpio.OUTPUT)
for i=1,numout do
    pwm.setup(pins[i], 100, 0)
    pwm.start(pins[i])
end


function receive(srv, pl) 
    cmd = string.byte(pl,2)
    handlers[cmd](string.sub(pl, 3))
end

handlers = {
  [PWM_CMD] = function(pl) parse_pwm(pl) end,
  [PATTERN_CMD] = function(pl) parse_pattern(pl) end
}


srv=net.createServer(net.UDP)
srv:on("receive", receive)   
srv:listen(port)
