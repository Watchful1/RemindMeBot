import utils
import logging


log = logging.getLogger("bot")


class Reminder:
	def __init__(
		self,
		source,
		message,
		user,
		requested_date,
		target_date=None,
		db_id=None,
		time_string=None
	):
		self.source = source
		self.message = message
		self.user = user
		self.requested_date = requested_date

		self.result_message = None
		self.valid = True

		if target_date is not None:
			self.target_date = target_date
		elif time_string is not None:
			self.target_date = utils.parse_time(time_string, requested_date)
			if self.target_date < utils.datetime_now():
				self.result_message = f"This time has already passed: {time_string}"
				log.warning(self.result_message)
				self.valid = False
		else:
			self.target_date = None

		if self.target_date is None:
			if time_string is None:
				self.result_message = "Could not find a time in message, defaulting to one day"
			else:
				self.result_message = f"Could not parse date: \"{time_string}\", defaulting to one day"
			log.info(self.result_message)
			self.target_date = utils.parse_time("1 day")

		self.db_id = db_id

	def render_confirmation(self):
		bldr = []
		if self.result_message is not None:
			bldr.append(self.result_message)
			bldr.append("\n\n")
		bldr.append("I will be messaging you on ")
		bldr.append(utils.render_time(self.target_date))
		bldr.append(" to remind you about: ")
		bldr.append(self.message)

		return bldr
