class Robot:
	DEFAULT_PID_INTEGRATION_LIMIT = 0

	def __init__(self):
		self.DT = 0.1

		self.kp = 1
		self.ki = 1
		self.kd = 1

		# velocidade linear objetivo
		self.rate_linear = 0
		# velocidade arngular objetivo
		self.rate_theta = 0

		self.error_linear = 0
		self.error_theta = 0

		self.prev_error_linear = 0
		self.prev_error_theta = 0

		self.last_theta = 0
		self.last_linear = 0

		self.integ_theta = 0
		self.integ_linear = 0

		self.power_left = 0
		self.power_right = 0

		

	def update(self, actual_linear, actual_theta):
		self.rate_theta = (actual_theta - self.last_theta)
		self.rate_linear = (actual_linear - self.last_linear)

		if (self.rate_theta > 180.0):
			self.rate_theta -= 360.0
		elif (self.rate_theta < -180.0):
			self.rate_theta += 360.0

		self.rate_theta = self.rate_theta / self.DT #dt

		self.last_theta = actual_theta

	def set_pid_lienar(self, kp, ki, kd, ilimit=DEFAULT_PID_INTEGRATION_LIMIT):
		self.integ_linear = 0
		self.prev_error_linear = 0

	def set_pid_theta(self, kp, ki, kd, ilimit=DEFAULT_PID_INTEGRATION_LIMIT):
		self.integ_theta = 0
		self.prev_error_theta = 0

	def get_pid_linear_speed(self, desired, _input, ilimit=DEFAULT_PID_INTEGRATION_LIMIT):
		self.error_linear = desired - _input
		self.integ_linear += self.error_linear * self.DT * self.ki

		if self.integ_linear > ilimit:
			self.integ_linear = ilimit
		elif self.integ_linear < ilimit:
			self.integ_linear = ilimit

		derivative = (self.error_linear - self.prev_error_linear)/self.DT

		speed_linear = self.kp * self.error_linear + self.kd * derivative + self.integ_linear

		self.prev_error_linear = self.error_linear

		return speed_linear



	def get_pid_linear_angular(self, desired, _input, ilimit=DEFAULT_PID_INTEGRATION_LIMIT):
		self.error_theta = desired - _input
		self.integ_theta += self.error_theta * self.DT * ki

		if self.integ_theta > ilimit:
			self.integ_theta = ilimit
		elif self.integ_theta < ilimit:
			self.integ_theta = ilimit

		derivative = (self.error_theta - self.prev_error_theta)/self.DT

		speed_theta = self.kp * self.error_theta + self.kd * derivative + self.integ_theta

		self.prev_error_theta = self.error_theta

		return speed_theta

	def speed_to_power(self, target_y, target_theta):
		speed_y = self.get_pid_linear_speed(target_y, self.rate_linear)
		speed_theta = self.get_pid_linear_speed(target_theta, self.rate_theta)

		acc_left = speed_y + speed_theta
		acc_right = speed_y - speed_theta

		self.power_left += acc_left * self.DT
		self.power_right += acc_right * self.DT

		self.power_left = min(100, max(-100, self.power_left))
		self.power_right = min(100, max(-100, self.power_right))

		self.error_linear = pow(speed_y - self.rate_linear, 2)
		self.error_theta = pow(speed_theta - self.rate_theta, 2)

		return (self.power_left, self.power_right)


