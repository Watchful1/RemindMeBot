import utils
import discord_logging
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

import static
from praw_wrapper import ReturnType
from database import Base
from database.UtcDateTime import UtcDateTime


log = discord_logging.get_logger()


class Reminder(Base):
	__tablename__ = 'reminders'

	id = Column(Integer, primary_key=True)
	source = Column(String(400), nullable=False)
	message = Column(String(500))
	user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
	requested_date = Column(UtcDateTime, nullable=False)
	target_date = Column(UtcDateTime, nullable=False)
	recurrence = Column(String(500))
	defaulted = Column(Boolean, nullable=False)

	comment = relationship("DbComment", cascade="all")
	user = relationship("User")

	def __init__(
		self,
		source,
		message,
		user,
		requested_date,
		target_date,
		recurrence=None,
		defaulted=False
	):
		self.source = source
		self.message = message
		self.user = user
		self.requested_date = requested_date
		self.target_date = target_date
		self.recurrence = recurrence
		self.defaulted = defaulted

	@staticmethod
	def build_reminder(
		source,
		message,
		user,
		requested_date,
		time_string,
		recurring=False,
		target_date=None,
		allow_default=True
	):
		result_message = None
		defaulted = False
		time_string = time_string.strip() if time_string is not None else None
		if target_date is None:
			if time_string is not None:
				target_date = utils.parse_time(time_string, requested_date, user.timezone)
				log.debug(f"Target date: {utils.get_datetime_string(target_date)}")

				if target_date is None:
					if allow_default:
						result_message = f"Could not parse date: \"{time_string}\", defaulting to one day"
						log.info(result_message)
						defaulted = True
						target_date = utils.parse_time("1 day", requested_date, None)

					else:
						result_message = f"Could not parse date: \"{time_string}\", defaulting not allowed"
						log.info(result_message)
						return None, result_message

				elif target_date < requested_date:
					result_message = f"This time, {time_string}, was interpreted as " \
						f"{utils.get_datetime_string(target_date)}, which is in the past"
					log.info(result_message)
					return None, result_message

			else:
				if allow_default:
					result_message = "Could not find a time in message, defaulting to one day"
					log.info(result_message)
					defaulted = True
					target_date = utils.parse_time("1 day", requested_date, None)

				else:
					result_message = f"Could not find a time in message, defaulting not allowed"
					log.info(result_message)
					return None, result_message

		if recurring:
			if defaulted:
				second_result_message = "Can't use a default for a recurring reminder"
				log.info(second_result_message)
				return None, result_message + "\n\n" + second_result_message

			else:
				second_target_date = utils.parse_time(time_string, target_date, user.timezone)
				log.debug(f"Second target date: {utils.get_datetime_string(second_target_date)}")
				if second_target_date == target_date:
					result_message = f"I've got {utils.get_datetime_string(target_date)} for your first date, but when" \
						f" I applied '{time_string}', I got the same date rather than one after it."
					log.info(result_message)
					return None, result_message

				elif second_target_date < target_date:
					result_message = f"I've got {utils.get_datetime_string(target_date)} for your first date, but when" \
						f" I applied '{time_string}', I got a date before that rather than one after it."
					log.info(result_message)
					return None, result_message

		reminder = Reminder(
			source=source,
			message=message,
			user=user,
			requested_date=requested_date,
			target_date=target_date,
			recurrence=time_string if recurring else None,
			defaulted=defaulted
		)

		return reminder, result_message

	def __str__(self):
		return f"{utils.get_datetime_string(self.requested_date)} " \
			f": {utils.get_datetime_string(self.target_date)} : {self.user.name} " \
			f": {self.source} : {self.message}"

	def is_cakeday(self):
		return self.message is not None and self.message == static.CAKEDAY_MESSAGE and \
			self.recurrence is not None and self.recurrence == "1 year"

	def render_message_confirmation(self, result_message, comment_return=None, pushshift_minutes=0):
		bldr = utils.str_bldr()
		if pushshift_minutes > 15 and comment_return is not None:
			bldr.append("There is a ")
			if pushshift_minutes > 60:
				bldr.append(str(int(round(pushshift_minutes / 60, 1))))
				bldr.append(" hour")
			else:
				bldr.append(str(int(pushshift_minutes)))
				bldr.append(" minute")
			bldr.append(" delay fetching comments.")
			bldr.append("\n\n")

		if result_message is not None:
			bldr.append(result_message)
			bldr.append("\n\n")

		if self.is_cakeday():
			bldr.append("I will message you every year at ")
			bldr.append(utils.render_time(self.target_date, self.user, "%m-%d %H:%M:%S %Z"))
			bldr.append(" to remind you of your cakeday.")

		else:
			if self.target_date < utils.datetime_now():
				bldr.append("I will be messaging you on ")
			else:
				bldr.append("I will be messaging you in ")
				bldr.append(utils.render_time_diff(utils.datetime_now(), self.target_date))
				bldr.append(" on ")
			bldr.append(utils.render_time(self.target_date, self.user))
			if self.recurrence is not None:
				bldr.append(" and then every `")
				bldr.append(self.recurrence)
				bldr.append("`")
			bldr.append(" to remind you")
			if self.message is None:
				bldr.append(" of [**this link**](")
				bldr.append(utils.check_append_context_to_link(self.source))
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

	def render_comment_confirmation(self, thread_id, count_duplicates=0, pushshift_minutes=0):
		bldr = utils.str_bldr()
		if pushshift_minutes > 15:
			bldr.append("There is a ")
			if pushshift_minutes > 60:
				bldr.append(str(int(round(pushshift_minutes / 60, 1))))
				bldr.append(" hour")
			else:
				bldr.append(str(pushshift_minutes))
				bldr.append(" minute")
			bldr.append(" delay fetching comments.")
			bldr.append("\n\n")

		if self.defaulted:
			bldr.append("**Defaulted to one day.**\n\n")

		if self.user.timezone is not None:
			bldr.append("Your [default time zone](")
			bldr.append(static.INFO_POST_SETTINGS)
			bldr.append(") is set to `")
			bldr.append(self.user.timezone)
			bldr.append("`. ")

		if self.is_cakeday():
			bldr.append("I will [message you every year](")
			bldr.append(static.INFO_POST_CAKEDAY)
			bldr.append(") at ")
			bldr.append(utils.render_time(self.target_date, self.user, "%m-%d %H:%M:%S %Z"))
			bldr.append(" to remind you of your cakeday.")

		else:
			if self.defaulted or self.target_date < utils.datetime_now():
				bldr.append("I will be messaging you on ")
			else:
				bldr.append("I will be messaging you in ")
				bldr.append(utils.render_time_diff(self.requested_date, self.target_date))
				bldr.append(" on ")
			bldr.append(utils.render_time(self.target_date, self.user))
			if self.recurrence is not None:
				bldr.append(" [and then every](")
				bldr.append(static.INFO_POST_REPEAT)
				bldr.append(") `")
				bldr.append(self.recurrence)
				bldr.append("`")
			bldr.append(" to remind you of [**this link**](")
			bldr.append(utils.replace_np(utils.check_append_context_to_link(self.source)))
			bldr.append(")")

		bldr.append("\n\n")

		bldr.append("[**")
		if count_duplicates > 0:
			bldr.append(str(count_duplicates))
			bldr.append(" OTHERS CLICKED")
		else:
			bldr.append("CLICK")
		bldr.append(" THIS LINK**](")
		bldr.append(utils.build_message_link(
			static.ACCOUNT_NAME,
			"Reminder",
			f"[{self.source}]\n\n{static.TRIGGER}! "
			f"{utils.get_datetime_string(self.target_date, format_string='%Y-%m-%d %H:%M:%S %Z')}"
		))
		bldr.append(") to send a PM to also be reminded and to reduce spam.")

		if thread_id is not None:
			bldr.append("\n\n")
			bldr.append("^(Parent commenter can ) [^(delete this message to hide from others.)](")
			bldr.append(utils.build_message_link(
				static.ACCOUNT_NAME,
				"Delete Comment",
				f"Delete! {thread_id}"
			))
			bldr.append(")")

		return bldr

	def render_notification(self):
		bldr = utils.str_bldr()
		bldr.append("RemindMeBot reminder here!")
		bldr.append("\n\n")

		if self.message is not None:
			bldr.append("I'm here to remind you:\n\n> ")
			bldr.append(self.message)
			bldr.append("\n\n")

		bldr.append("The source comment or message:\n\n>")
		bldr.append(utils.check_append_context_to_link(self.source))
		bldr.append("\n\n")

		if self.requested_date is None:
			bldr.append("This reminder was created before I started saving the creation date of reminders.")
		else:
			bldr.append("You requested this reminder on: ")
			bldr.append(utils.render_time(self.requested_date, self.user))
		bldr.append("\n\n")

		if self.recurrence is not None:
			if self.user.recurring_sent > static.RECURRING_LIMIT:
				bldr.append("I've sent you at least ")
				bldr.append(str(static.RECURRING_LIMIT))
				bldr.append(" recurring reminders since I last heard from you, so I'm automatically canceling this reminder. ")
				bldr.append("[Click here](")
				bldr.append(utils.build_message_link(
					static.ACCOUNT_NAME,
					"ReminderRepeat",
					f"[{(self.message[:500] if self.message is not None else self.source)}]\n\n{static.TRIGGER_RECURRING}! {self.recurrence}"
				))
				bldr.append(") to recreate it.")
			else:
				if self.is_cakeday():
					bldr.append("I will message you every year at ")
					bldr.append(utils.render_time(self.target_date, self.user, "%m-%d %H:%M:%S %Z"))
					bldr.append(" to remind you of your cakeday.")

				else:
					bldr.append("This is a repeating reminder. I'll message you again in `")
					bldr.append(self.recurrence)
					bldr.append("`, which is ")
					bldr.append(utils.render_time(utils.parse_time(self.recurrence, self.target_date, self.user.timezone), self.user))
					bldr.append(".")

			bldr.append("\n\n")

			bldr.append("[Click here](")
			bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove", f"Remove! {self.id}"))
			bldr.append(") to delete this reminder.")

		else:
			bldr.append("[Click here](")
			bldr.append(utils.build_message_link(
				static.ACCOUNT_NAME,
				"Reminder",
				f"[{(self.message[:500] if self.message is not None else self.source)}]\n\n{static.TRIGGER}! "
			))
			bldr.append(") and set the time after the ")
			bldr.append(static.TRIGGER)
			bldr.append(" command to be reminded of the original comment again.")

		return bldr
