-- udp listen port.
-- protocol is easy:
--      2 byte for cmd. first is not used, second is CMD
--      2 bytes per output, first byte is MSB. in order.
port = 5555

PWM_CMD = 126 -- 0x7e

-- pins in ascending order of frequency ranges and total of pins.
pins = { 8, 4, 3, 2, 1 }

-- minimal duty cycle. zero for default off
min = 0

-- max duty cycle. above 1023 will err.
max = 1023

-- afterglow
glow = false
reduce = 20

-- gpio.mode(pin,gpio.OUTPUT)
for i=1,#pins do
    pwm.setup(pins[i], 100, 0)
    pwm.start(pins[i])
end

function read2b(bstr)
    return (string.byte(bstr,1)*256 + string.byte(bstr,2))
end

srv=net.createServer(net.UDP)
srv:on("receive", function(srv, pl)
    cmd = read2b(pl)
    -- print("pwm cmd")
    if(cmd == PWM_CMD) then
    for i=1,#pins do 
        val = read2b(string.sub(pl,1+2*i)) + min
        if(val > max) 
            then pwm.setduty(pins[i], max)
            else
              if(glow)
                then
                 before = pwm.getduty(pins[i])
                 if((val+min) < before - reduce)
                  then pwm.setduty(pins[i], before-reduce)
                  else pwm.setduty(pins[i], val)
                 end
                else
                 pwm.setduty(pins[i], val)
              end
        end
     end
     end
   end)
   
srv:listen(port)
