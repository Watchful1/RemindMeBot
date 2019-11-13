import discord_logging
import re
import traceback
import pytz

import utils
import static
from classes.reminder import Reminder
from classes.enums import ReturnType


log = discord_logging.get_logger()


def get_reminders_string(user_name, database, previous=False):
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
				if reminders[0].recurrence is not None:
					bldr.append("|Source|Message|Date|In|Repeat|Remove|\n")
					bldr.append("|-|-|-|-|-|:-:|\n")
				else:
					bldr.append("|Source|Message|Date|In|Remove|\n")
					bldr.append("|-|-|-|-|:-:|\n")

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
					bldr.append(utils.render_time(reminder.target_date, reminder.user.timezone))
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
						log.warning(f"Too many reminders for u/{user_name}: {len(regular_reminders)} : {len(recurring_reminders)}")
						bldr.append("\nToo many reminders to display.")
						break

				bldr.append("\n")

	else:
		bldr.append("You don't have any reminders.")

	return bldr


def process_remind_me(message, database, recurring):
	log.info("Processing RemindMe message")
	time = utils.find_reminder_time(message.body, recurring)

	message_text = utils.find_reminder_message(message.body, recurring)

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
		return [result_message]

	database.add_reminder(reminder)

	log.info(f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}")

	return reminder.render_message_confirmation(result_message)


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

	return bldr


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

	return bldr


def process_get_reminders(message, database):
	log.info("Processing get reminders message")
	return get_reminders_string(message.author.name, database)


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

	return bldr


def process_cakeday_message(message, database):
	log.info("Processing cakeday")

	if database.user_has_cakeday_reminder(message.author.name):
		log.info("Cakeday already exists")
		return ["It looks like you already have a cakeday reminder set."]

	next_anniversary = utils.get_next_anniversary(message.author.created_utc)

	reminder = Reminder(
		source=utils.message_link(message.id),
		message=static.CAKEDAY_MESSAGE,
		user=database.get_or_add_user(message.author.name),
		requested_date=utils.datetime_from_timestamp(message.created_utc),
		target_date=next_anniversary,
		recurrence="one year",
		defaulted=False
	)

	database.add_reminder(reminder)

	log.info(f"Cakeday reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}")

	return reminder.render_message_confirmation(None)


def process_timezone_message(message, database):
	log.info("Processing timezone")
	bldr = utils.str_bldr()

	timezones = re.findall(r'(?:timezone!? )([\w/]{1,50})', message.body, flags=re.IGNORECASE)
	if len(timezones) == 0:
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

	return bldr


def process_message(message, reddit, database, count_string=""):
	if message.author is None:
		log.info(f"Subreddit message, skipping : {message.id}")
		return
	log.info(f"{count_string}: Message u/{message.author.name} : {message.id}")
	user = database.get_or_add_user(message.author.name)
	user.recurring_sent = 0
	body = message.body.lower()

	bldr = None
	if static.TRIGGER_RECURRING_LOWER in body:
		bldr = process_remind_me(message, database, True)
	elif static.TRIGGER_LOWER in body:
		bldr = process_remind_me(message, database, False)
	elif "myreminders!" in body:
		bldr = process_get_reminders(message, database)
	elif "remove!" in body:
		bldr = process_remove_reminder(message, database)
	elif "removeall!" in body:
		bldr = process_remove_all_reminders(message, database)
	elif "delete!" in body:
		bldr = process_delete_comment(message, reddit, database)
	elif "cakeday!" in body:
		bldr = process_cakeday_message(message, database)
	elif "timezone!" in body:
		bldr = process_timezone_message(message, database)

	if bldr is None:
		bldr = ["I couldn't find anything in your message."]

	bldr.extend(utils.get_footer())
	result = reddit.reply_message(message, ''.join(bldr))
	if result != ReturnType.SUCCESS:
		if result == ReturnType.INVALID_USER:
			log.info("User banned before reply could be sent")
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
		if reddit.is_message(message):
			if message.author is None:
				log.info(f"Message {message.id} is a system notification")
			elif message.author.name == "reddit":
				log.info(f"Message {message.id} is from reddit, skipping")
			else:
				try:
					process_message(message, reddit, database, f"{i}/{len(messages)}")
				except Exception:
					log.warning(f"Error processing message: {message.id} : u/{message.author.name}")
					log.warning(traceback.format_exc())
				finally:
					database.commit()
		else:
			log.info(f"Object not message, skipping: {message.id}")

		try:
			reddit.mark_read(message)
		except Exception:
			log.warning(f"Error marking message read: {message.id} : {message.author.name}")
			log.warning(traceback.format_exc())

	return len(messages)
