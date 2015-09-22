-- Configure UART to 115200 8N1
uart.setup(0, 115200, 8, 0, 1, 1)

require('config')
require('pca9685')


-- Initialize I2C bus with SDA and SCL from config 
-- https://github.com/nodemcu/nodemcu-firmware/wiki/nodemcu_api_en#new_gpio_map
i2c.setup(i2c_id, i2c_sda, i2c_scl, i2c.SLOW)

-- Initialize PCA9685 PWM controller
-- Args:
--	i2c bus id (should be 0)
--	i2c address (see pca9685 datasheet)
--	mode - 16-bit value, low byte is MODE1, high is MODE2 (see datasheet)
--
-- TODO: maybe use auto incrementing control register?
for i = 1,getn(pca9685_addr) do
  pca9685.init(i2c_id, pwm_ctrl_addr[i], 0)
end

-- PWM channels used for R, G, B colors. 
pwm_channels={0, 1, 2}

-- Setup Wi-Fi connection
wifi.setmode(wifi.STATION)
wifi.sta.config('HomeNetwork', 'VerySecretPassword')

-- MQTT parameters
-- Will subscribe to messages on topic <mqtt_topic>/rgb
-- Publish a message with hex color value (e.g. "ff00ff" - purple)
mqtt_host='192.168.0.1'
mqtt_port='1883'
mqtt_user='test'
mqtt_password='test'
mqtt_secure=0
mqtt_clientid='room-rgbstrip'	-- Default: "esp8266_<MACADDR>"
mqtt_topic='/room/rgbstrip'		-- Default: "/<clientid>"

dofile('server.lc')
