class State:

	strips = None

	def __init__(self, strips):
		self.strips = strips
		
	def state_off(self):
		"""Return a state in which all strips are off."""
		return [[0, 0, 0] for i in range(self.strips)]

	def full_color(self, color):
		"""Return a state with all strips set to color."""
		return [color for i in range(self.strips)]
	
	def set_strips(self, state, strips, color):
		"""Return a state in which given strips are set to color."""
		for i in strips:
			state[i] = color
		return state