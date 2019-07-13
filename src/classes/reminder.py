import utils
import discord_logging

import static
from classes.enums import ReturnType


log = discord_logging.get_logger()


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
		count_duplicates=0,
		thread_id=None,
		defaulted=False
	):
		self.source = source
		self.message = message
		self.user = user
		self.requested_date = requested_date
		self.count_duplicates = count_duplicates
		self.thread_id = thread_id

		self.result_message = None
		self.valid = True
		self.defaulted = defaulted

		if target_date is not None:
			self.target_date = target_date
		elif time_string is not None:
			self.target_date = utils.parse_time(time_string, requested_date)

			if self.target_date is not None and self.target_date < self.requested_date:
				self.result_message = f"This time, {time_string.strip()}, was interpreted as " \
					f"{utils.get_datetime_string(self.target_date)}, which is in the past"
				log.info(self.result_message)
				self.valid = False
		else:
			self.target_date = None

		if self.target_date is None:
			if time_string is None:
				self.result_message = "Could not find a time in message, defaulting to one day"
			else:
				self.result_message = f"Could not parse date: \"{time_string.strip()}\", defaulting to one day"
			log.info(self.result_message)
			self.defaulted = True
			self.target_date = utils.parse_time("1 day", requested_date)

		self.db_id = db_id

	def __str__(self):
		return f"{utils.get_datetime_string(self.requested_date)} " \
			f": {utils.get_datetime_string(self.target_date)} : {self.user} " \
			f": {self.source} : {self.message}"

	def render_message_confirmation(self, timezone, comment_return=None):
		bldr = utils.str_bldr()
		if self.result_message is not None:
			bldr.append(self.result_message)
			bldr.append("\n\n")
		bldr.append("I will be messaging you on ")
		bldr.append(utils.render_time(self.target_date, timezone))
		bldr.append(" to remind you")
		if self.message is None:
			bldr.append(" of [**this link**](")
			bldr.append(self.source)
			bldr.append(")")
		else:
			bldr.append(": ")
			bldr.append(self.message)

		if comment_return is not None and comment_return in (
			ReturnType.FORBIDDEN,
			ReturnType.THREAD_LOCKED,
			ReturnType.DELETED_COMMENT,
			ReturnType.RATELIMIT,
			ReturnType.THREAD_REPLIED
		):
			bldr.append("\n\n")
			bldr.append("I'm sending this to you as a message instead of replying to your comment because ")
			if comment_return == ReturnType.FORBIDDEN:
				bldr.append("I'm not allowed to reply in this subreddit.")
			elif comment_return == ReturnType.THREAD_LOCKED:
				bldr.append("the thread is locked.")
			elif comment_return == ReturnType.DELETED_COMMENT:
				bldr.append("it was deleted before I could get to it.")
			elif comment_return == ReturnType.RATELIMIT:
				bldr.append("I'm new to this subreddit and have already replied to another thread here recently.")
			elif comment_return == ReturnType.THREAD_REPLIED:
				bldr.append("I've already replied to another comment in this thread.")

		return bldr

	def render_comment_confirmation(self):
		bldr = utils.str_bldr()

		if self.defaulted:
			bldr.append("**Defaulted to one day.**\n\n")

		bldr.append("I will be messaging you on ")
		bldr.append(utils.render_time(self.target_date))
		bldr.append(" to remind you of [**this link**](")
		bldr.append(utils.replace_np(self.source))
		bldr.append(")")

		bldr.append("\n\n")

		bldr.append("[**")
		if self.count_duplicates > 0:
			bldr.append(str(self.count_duplicates))
			bldr.append(" OTHERS CLICKED")
		else:
			bldr.append("CLICK")
		bldr.append(" THIS LINK**](")
		bldr.append(utils.build_message_link(
			static.ACCOUNT_NAME,
			"Reminder",
			f"[{self.source}]\n\n{static.TRIGGER}! {utils.get_datetime_string(self.target_date)}"
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

		return bldr

	def render_notification(self, timezone):
		bldr = utils.str_bldr()

		bldr.append("RemindMeBot reminder here!")
		bldr.append("\n\n")

		if self.message is not None:
			bldr.append("I'm here to remind you:\n\n> ")
			bldr.append(self.message)
			bldr.append("\n\n")

		bldr.append("The source comment or message:\n\n>")
		bldr.append(self.source)
		bldr.append("\n\n")

		if self.requested_date is None:
			bldr.append("This reminder was created before I started saving the creation date of reminders.")
		else:
			bldr.append("You requested this reminder on: ")
			bldr.append(utils.render_time(self.requested_date, timezone))
		bldr.append("\n\n")

		bldr.append("[Click here](")
		bldr.append(utils.build_message_link(
			static.ACCOUNT_NAME,
			"Reminder",
			f"[{self.message}]\n\n{static.TRIGGER}! "
		))
		bldr.append(") and set the time after the ")
		bldr.append(static.TRIGGER)
		bldr.append(" command to be reminded of the original comment again.")

		return bldr
