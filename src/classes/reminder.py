import utils
import logging

import static


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
		time_string=None,
		count_duplicates=1,
		thread_id=None
	):
		self.source = source
		self.message = message
		self.user = user
		self.requested_date = requested_date
		self.count_duplicates = count_duplicates
		self.thread_id = thread_id

		self.result_message = None
		self.valid = True

		if target_date is not None:
			self.target_date = target_date
		elif time_string is not None:
			self.target_date = utils.parse_time(time_string, requested_date)
			if self.target_date < self.requested_date:
				self.result_message = f"This time is in the past: {time_string}"
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

	def render_message_confirmation(self):
		bldr = utils.str_bldr()
		if self.result_message is not None:
			bldr.append(self.result_message)
			bldr.append("\n\n")
		bldr.append("I will be messaging you on ")
		bldr.append(utils.render_time(self.target_date))
		bldr.append(" to remind you")
		if self.message is None:
			bldr.append(" of [**this link**](")
			bldr.append(self.source)
			bldr.append(")")
		else:
			bldr.append(": ")
			bldr.append(self.message)

		return bldr

	def render_comment_confirmation(self):
		bldr = utils.str_bldr()
		bldr.append("I will be messaging you on ")
		bldr.append(utils.render_time(self.target_date))
		bldr.append(" to remind you of [**this link**](")
		bldr.append(utils.replace_np(self.source))
		bldr.append(")")

		bldr.append("\n\n")

		bldr.append("[**")
		if self.count_duplicates <= 1:
			bldr.append(str(self.count_duplicates))
			bldr.append(" OTHERS CLICKED")
		else:
			bldr.append("CLICK")
		bldr.append(" THIS LINK**](")
		bldr.append(utils.build_message_link(
			static.ACCOUNT_NAME,
			"Reminder",
			f"[{self.source}]\n\nRemindMe! {utils.get_datetime_string(self.target_date)}"
		))
		bldr.append(") to send a PM to also be reminded and to reduce spam.")

		if self.thread_id is not None:
			bldr.append("\n\n")
			bldr.append("^(Parent commenter can ) [^(delete this message to hide from others.)](")
			bldr.append(utils.build_message_link(
				static.ACCOUNT_NAME,
				"Delete Comment",
				f"Delete! {self.thread_id}"
			))
			bldr.append(")")
