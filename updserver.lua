port = 5555
pin = 4


gpio.mode(pin,gpio.OUTPUT)


srv=net.createServer(net.UDP)
srv:on("receive", function(srv, pl)
--   print("Command Received")
   bytes = nil
   byte = string.byte(pl,1)
--   print(byte)
   if (byte > 10)
        then gpio.write(pin, gpio.HIGH)
        else gpio.write(pin, gpio.LOW)
   end
--   if pl=="on" then gpio.write(pin, gpio.HIGH) else gpio.write(pin, gpio.LOW) end
   end)
srv:listen(port)