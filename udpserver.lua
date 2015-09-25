port = 5555
pins = { 8, 4 }
numout = 2
min = 65
max = 1023

glow = true
reduce = 20

-- gpio.mode(pin,gpio.OUTPUT)
for i=1,numout do
    pwm.setup(pins[i], 100, 0)
    pwm.start(pins[i])
end

srv=net.createServer(net.UDP)
srv:on("receive", function(srv, pl)
--   print("Command Received")
    bytes = nil
    for i=1,numout do 
        byte = string.byte(pl,i)
--   print(byte)
        if(30*byte > max-min)
             --gpio.write(pin, gpio.HIGH)
            then pwm.setduty(pins[i], max)
            else
              if(glow)
                then
                 before = pwm.getduty(pins[i])
                 if((30*byte+min) < before - reduce)
                  then pwm.setduty(pins[i], before-reduce)
                  else pwm.setduty(pins[i], 30*byte+min)
                 end
                else
                 pwm.setduty(pins[i], 30*byte+min)
              end
        end
     end
   end)
   
srv:listen(port)