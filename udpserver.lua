-- udp listen port.
-- protocol is easy:
--      2 byte for cmd. first is not used, second is CMD
--      2 bytes per output, first byte is MSB. in order.
port = 5555

PWM_CMD = 126 -- 0x7e

-- pins in ascending order of frequency ranges and total of pins.
pins = { 8, 4, 3, 2, 1 }
numout = 5

-- minimal duty cycle. zero for default off
min = 65

-- max duty cycle. above 1023 will err.
max = 1023

-- afterglow
glow = true
reduce = 20

-- gpio.mode(pin,gpio.OUTPUT)
for i=1,numout do
    pwm.setup(pins[i], 100, 0)
    pwm.start(pins[i])
end

srv=net.createServer(net.UDP)
srv:on("receive", function(srv, pl)
    cmd = string.byte(pl,2)
    if(cmd ~= PWM_CMD) then return else
--   print("Command Received")
    for i=1,numout do 
        byte = string.byte(pl,2 + i*2)*256 + string.byte(pl,2 + i*2+1)
--   print(byte)
        if(byte > max-min) 
             --gpio.write(pin, gpio.HIGH)
            then pwm.setduty(pins[i], max)
            else
              if(glow)
                then
                 before = pwm.getduty(pins[i])
                 if((byte+min) < before - reduce)
                  then pwm.setduty(pins[i], before-reduce)
                  else pwm.setduty(pins[i], byte+min)
                 end
                else
                 pwm.setduty(pins[i], byte+min)
              end
        end
     end
     end
   end)
   
srv:listen(port)
