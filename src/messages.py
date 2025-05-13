import discord_logging
import re
import traceback
import pytz

import utils
import static
import counters
from classes.reminder import Reminder
from praw_wrapper.reddit import ReturnType


log = discord_logging.get_logger()


def add_list_header(bldr, recurring):
	if recurring:
		bldr.append("|Source|Message|Date|In|Repeat|Remove|\n")
		bldr.append("|-|-|-|-|-|:-:|\n")
	else:
		bldr.append("|Source|Message|Date|In|Remove|\n")
		bldr.append("|-|-|-|-|:-:|\n")


def get_reminders_string(user_name, database, previous=False, include_all=False):
	result_messages = []
	bldr = utils.str_bldr()

	regular_reminders, recurring_reminders = database.get_user_reminders(user_name)
	if len(regular_reminders) or len(recurring_reminders):
		if previous:
			bldr.append("Your previous reminders:")
		else:
			bldr.append("Your current reminders:")
		bldr.append("\n\n")

		if len(regular_reminders) + len(recurring_reminders) > 1:
			bldr.append("[Click here to delete all your reminders](")
			bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove All", "RemoveAll!"))
			bldr.append(")\n\n")

		user = database.get_or_add_user(user_name)
		if user.timezone is not None:
			bldr.append("Your timezone is currently set to: `")
			bldr.append(user.timezone)
			bldr.append("`\n\n")

		for reminders in [recurring_reminders, regular_reminders]:
			if len(reminders):
				log.debug(f"Building list with {len(reminders)} reminders")
				add_list_header(bldr, reminders[0].recurrence is not None)

				for reminder in reminders:
					bldr.append("|")
					if "reddit.com" in reminder.source:
						bldr.append("[Source](")
						bldr.append(utils.check_append_context_to_link(reminder.source))
						bldr.append(")")
					else:
						bldr.append(reminder.source)
					bldr.append("|")
					if reminder.message is not None:
						bldr.append(reminder.message.replace("|", "&#124;"))
					bldr.append("|")
					bldr.append(utils.render_time(reminder.target_date, reminder.user))
					bldr.append("|")
					bldr.append(utils.render_time_diff(utils.datetime_now(), reminder.target_date))
					if reminder.recurrence is not None:
						bldr.append("|")
						bldr.append(reminder.recurrence)
					bldr.append("|")
					bldr.append("[Remove](")
					bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove", f"Remove! {reminder.id}"))
					bldr.append(")")
					bldr.append("|\n")

					if utils.bldr_length(bldr) > 9000:
						if include_all:
							result_messages.append(''.join(bldr))
							bldr = []
							add_list_header(bldr, reminders[0].recurrence is not None)
						else:
							bldr.append("\nToo many reminders to display.")
							break

				bldr.append("\n")

	else:
		bldr.append("You don't have any reminders.")

	result_messages.append(''.join(bldr))
	return result_messages


def process_remind_me(message, reddit, database, recurring):
	log.info("Processing RemindMe message")
	trigger = static.TRIGGER_RECURRING_LOWER if recurring else static.TRIGGER_LOWER
	time = utils.find_reminder_time(message.body, trigger)

	message_text = utils.find_reminder_message(message.body, trigger)

	reminder, result_message = Reminder.build_reminder(
		source=utils.message_link(message.id),
		message=message_text,
		user=database.get_or_add_user(message.author.name),
		requested_date=utils.datetime_from_timestamp(message.created_utc),
		time_string=time,
		recurring=recurring
	)
	if reminder is None:
		log.debug("Reminder not valid, returning")
		return [result_message], False

	database.add_reminder(reminder)
	database.commit()

	log.info(f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}")

	bldr = reminder.render_message_confirmation(result_message)
	return [''.join(bldr)], True


def process_remove_reminder(message, database):
	log.info("Processing remove reminder message")
	bldr = utils.str_bldr()

	ids = re.findall(r'remove!\s(\d+)', message.body, flags=re.IGNORECASE)
	if len(ids) == 0:
		bldr.append("I couldn't find a reminder id to remove.")
	else:
		reminder = database.get_reminder(ids[0])
		if reminder is None or reminder.user.name != message.author.name:
			bldr.append("It looks like you don't own this reminder or it doesn't exist.")
		else:
			database.delete_reminder(reminder)
			bldr.append("Reminder deleted.")

	bldr.append("\n\n")
	bldr.append("*****")
	bldr.append("\n\n")

	bldr.extend(get_reminders_string(message.author.name, database))

	return [''.join(bldr)]


def process_remove_all_reminders(message, database):
	log.info("Processing remove all reminders message")

	current_reminders = get_reminders_string(message.author.name, database, True)

	reminders_deleted = database.delete_user_reminders(message.author.name)
	log.debug(f"Deleted {reminders_deleted} reminders")

	bldr = utils.str_bldr()
	if reminders_deleted != 0:
		bldr.append("Deleted **")
		bldr.append(str(reminders_deleted))
		bldr.append("** reminders.\n\n")

	bldr.append("\n\n")
	bldr.append("*****")
	bldr.append("\n\n")

	bldr.extend(current_reminders)

	return [''.join(bldr)]


def process_get_reminders(message, database):
	log.info("Processing get reminders message")
	return get_reminders_string(message.author.name, database, include_all=True)


def process_delete_comment(message, reddit, database):
	log.info("Processing delete comment")
	bldr = utils.str_bldr()

	ids = re.findall(r'delete!\s(\w+)', message.body, flags=re.IGNORECASE)
	if len(ids) == 0:
		log.debug("Couldn't find a thread id to delete")
		bldr.append("I couldn't find a thread id to delete.")
	else:
		db_comment = database.get_comment_by_thread(ids[0])
		if db_comment is not None:
			if db_comment.user == message.author.name:
				comment = reddit.get_comment(db_comment.comment_id)
				if not reddit.delete_comment(comment):
					log.debug(f"Unable to delete comment: {db_comment.comment_id}")
					bldr.append("Something went wrong deleting the comment")
				else:
					database.delete_comment(db_comment)
					log.debug(f"Deleted comment: {db_comment.comment_id}")
					bldr.append("Comment deleted.")
			else:
				log.debug(f"Bot wasn't replying to owner: {db_comment.user} : {message.author.name}")
				bldr.append("It looks like the bot wasn't replying to you.")
		else:
			log.debug(f"Comment doesn't exist: {ids[0]}")
			bldr.append("This comment doesn't exist or was already deleted.")

	return [''.join(bldr)]


def process_cakeday_message(message, reddit, database):
	log.info("Processing cakeday")

	if database.user_has_cakeday_reminder(message.author.name):
		log.info("Cakeday already exists")
		return ["It looks like you already have a cakeday reminder set."], False

	next_anniversary = utils.get_next_anniversary(message.author.created_utc)

	reminder = Reminder(
		source=utils.message_link(message.id),
		message=static.CAKEDAY_MESSAGE,
		user=database.get_or_add_user(message.author.name),
		requested_date=utils.datetime_from_timestamp(message.created_utc),
		target_date=next_anniversary,
		recurrence="1 year",
		defaulted=False
	)

	database.add_reminder(reminder)
	database.commit()

	log.info(f"Cakeday reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}")

	bldr = reminder.render_message_confirmation(None)
	return [''.join(bldr)], True


def process_timezone_message(message, database):
	log.info("Processing timezone")
	bldr = utils.str_bldr()

	timezones = re.findall(r'(?:timezone!? )([\w/]{1,50})', message.body, flags=re.IGNORECASE)
	if not len(timezones):
		log.debug("Couldn't find a timezone in your message")
		bldr.append("I couldn't find a timezone in your message.")

	elif timezones[0] not in pytz.common_timezones:
		log.debug(f"Invalid timezone: {timezones[0]}")
		bldr.append(f"{timezones[0]} is not a valid timezone.")

	else:
		user = database.get_or_add_user(message.author.name)
		if timezones[0] == "UTC":
			user.timezone = None
			bldr.append(f"Reset your timezone to the default")
		else:
			user.timezone = timezones[0]
			bldr.append(f"Updated your timezone to {timezones[0]}")

		log.info(f"u/{message.author.name} timezone updated to {timezones[0]}")

	return [''.join(bldr)]


def process_clock_message(message, database):
	log.info("Processing clock")
	bldr = utils.str_bldr()

	clocks = re.findall(r'(?:clock!? +)([\d]{2})', message.body, flags=re.IGNORECASE)
	if not len(clocks):
		log.debug("Couldn't find a clock type in your message")
		bldr.append("I couldn't find a clock type in your message.")

	else:
		user = database.get_or_add_user(message.author.name)
		if clocks[0] == "24":
			user.time_format = None
			bldr.append(f"Reset your clock type to the default 24 hour clock")
		elif clocks[0] == "12":
			user.time_format = "12"
			bldr.append(f"Updated your clock type to a 12 hour clock")
		else:
			log.debug(f"Invalid clock type: {clocks[0]}")
			bldr.append(f"{clocks[0]} is not a valid clock type.")
			return bldr

		log.info(f"u/{message.author.name} clock type updated to {clocks[0]}")

	return [''.join(bldr)]


def process_message(message, reddit, database, count_string=""):
	log.info(f"{count_string}: Message u/{message.author.name} : {message.id}")
	user = database.get_or_add_user(message.author.name)
	user.recurring_sent = 0
	body = message.body.lower()

	result_messages = None
	created = False
	if static.TRIGGER_RECURRING_LOWER in body:
		result_messages, created = process_remind_me(message, reddit, database, True)
		if created:
			counters.replies.labels(source='message', type='repeat').inc()
	elif static.TRIGGER_LOWER in body:
		result_messages, created = process_remind_me(message, reddit, database, False)
		if created:
			counters.replies.labels(source='message', type='single').inc()
	elif "myreminders!" in body:
		result_messages = process_get_reminders(message, database)
	elif "remove!" in body:
		result_messages = process_remove_reminder(message, database)
	elif "removeall!" in body:
		result_messages = process_remove_all_reminders(message, database)
	elif "delete!" in body:
		result_messages = process_delete_comment(message, reddit, database)
	elif "cakeday!" in body:
		result_messages, created = process_cakeday_message(message, reddit, database)
		if created:
			counters.replies.labels(source='message', type='cake').inc()
	elif "timezone!" in body:
		result_messages = process_timezone_message(message, database)
	elif "clock!" in body:
		result_messages = process_clock_message(message, database)

	if not created:
		counters.replies.labels(source='message', type='other').inc()

	if result_messages is None:
		result_messages = ["I couldn't find anything in your message."]

	result_messages[-1] = result_messages[-1] + ''.join(utils.get_footer())
	for result_message in result_messages:
		result = reddit.reply_message(message, result_message, retry_seconds=600)
		if result != ReturnType.SUCCESS:
			if result == ReturnType.INVALID_USER:
				log.info("User banned before reply could be sent")
				break
			else:
				raise ValueError(f"Error sending message: {result.name}")

	database.commit()


def process_messages(reddit, database):
	messages = reddit.get_messages()
	if len(messages):
		log.debug(f"Processing {len(messages)} messages")
	i = 0
	for message in messages[::-1]:
		i += 1
		mark_read = True
		if reddit.is_message(message):
			if message.author is None:
				log.info(f"Message {message.id} is a system notification")
			elif message.author.name == "reddit":
				log.info(f"Message {message.id} is from reddit, skipping")
			elif message.author.name in static.BLACKLISTED_ACCOUNTS:
				log.info(f"Message {message.id} from u/{message.author.name} is blacklisted, skipping")
			else:
				try:
					process_message(message, reddit, database, f"{i}/{len(messages)}")
				except Exception as err:
					mark_read = not utils.process_error(
						f"Error processing message: {message.id} : u/{message.author.name}",
						err, traceback.format_exc()
					)
				finally:
					database.commit()
		else:
			log.info(f"Object not message, skipping: {message.id}")

		if mark_read:
			try:
				reddit.mark_read(message)
			except Exception as err:
				utils.process_error(
					f"Error marking message read: {message.id} : {message.author.name}",
					err, traceback.format_exc()
				)

	return len(messages)
