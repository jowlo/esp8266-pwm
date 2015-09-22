local modname = ...
local M = {}
_G[modname] = M

local id = nil
local addr = nil


-- some flags from mode register, low byte is MODE1 and high is MODE2
-- Inverted output logic 
M.INVERT = 0x1000
-- For use with external driver, outputs set to totem pole (default)
M.OUTDRV = 0x0400




-- Standard mode values
M.MODE1 = 0x21  -- 0010 0001 (register auto increment after r/w-operation 
                -- enabled, ALLCALL address [0xe0 = 1110 0000] activated)
M.MODE2 = 0x04  -- 0000 0100 (totem pole mode)


-- TODO: remove if never needed?
local function read_reg(reg)
	i2c.start(id)
	if not i2c.address(id, addr, i2c.TRANSMITTER) then
		return nil
	end
	i2c.write(id, reg)
	i2c.stop(id)
	i2c.start(id)
	if not i2c.address(id, addr, i2c.RECEIVER) then
		return nil
	end
	c = i2c.read(id, 1)
	i2c.stop(id)
	return c:byte(1)
end


-- TODO: Do not send stop condition but keep writing to other controller if needed
--       By default outputs are updated on STOP, not on ACK
local function write_reg(i2c_id, i2c_addr, reg, ...)
	i2c.start(i2c_id)
	if not i2c.address(i2c_id, i2c_addr, addr, i2c.TRANSMITTER) then
		return nil
	end
	i2c.write(i2c_id, reg)
	len = i2c.write(id, ...)
	i2c.stop(i2c_id)
	return len
end

-- Initialize PCA9685
-- 
-- Set both mode registers
-- NOTE: Cannot use auto-increment here, but could save (at least) one stop condition
function M.init(i2c_id, i2c_addr, mode)
	if write_reg(i2c_id, i2c_addr, 0, bit.bor(M.MODE1, bit.band(mode, 0xFF))) ~= 1 then
		return nil
	end
	if write_reg(i2c_id, i2c_addr, 1, bit.bor(M.MODE2, bit.band(bit.rshift(mode, 8), 0xFF))) ~= 1 then
		return nil
	end
end

-- Calculate Channel register
--  chan: channel number (0-15)
--  reg: offset
local function chan_reg(chan, reg)
	return 6 + chan*4 + reg;
end

-- Set full on registry to value of 'on'-parameter
function M.set_chan_on(chan, on)
	return write_reg(chan_reg(chan, 1), 0x10 * on)
end

-- Set full off registry to value of 'off'-parameter
function M.set_chan_off(chan, off)
	return write_reg(chan_reg(chan, 3), 0x10 * off)
end

-- Set PWM on chan with on and off values
-- NOTE: Added and-mask on second and fourth register to reset full_on/full_off pins.
--       Don't know if needed.
-- TODO: Check and remove note
function M.set_chan_pwm(chan, on, off)
	return write_reg(chan_reg(chan, 0),
             bit.band(on, 0xFF),                -- Set LSBs for on timer
             bit.band(bit.rshift(on, 8), 0x0F), -- Set MSBs for on timer disabling full on
             bit.band(off, 0xFF),               -- Set LSBs for off timer
             bit.band(bit.rshift(off, 8), 0x0F) -- Set MSBs for off timer disabling full off
          )
end


-- Set channel to scaled value between 0 and max.
-- Where 0 switches off and max sets to full 
-- TODO: Setting multiple channels (for use without STOP)
local function set_chan_scaled(chan, max, val)
	if (val < 0) or (val > max) or (val == nil) or (max == nil) then
		return nil
	end
	if val == 0 then
		M.set_chan_on(chan, 0)
		M.set_chan_off(chan, 1)
	elseif val == max then
		M.set_chan_on(chan, 1)
		M.set_chan_off(chan, 0)
	else
		return M.set_chan_pwm(chan, 0, 4096*val/max)
	end
end

-- Convenience percentage setting
function M.set_chan_percent(chan, val)
	return set_chan_scaled(chan, 100, val)
end

-- Convenience bytewise setting (i guess for servos?)
function M.set_chan_byte(chan, val)
	return set_chan_scaled(chan, 255, val)
end

return M
