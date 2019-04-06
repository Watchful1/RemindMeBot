import logging
from datetime import datetime

import utils
import static
from classes.reminder import Reminder

log = logging.getLogger("bot")


def process_remind_me(message, database):
	log.info("Processing RemindMe message")
	time = utils.find_time(message.body)
	if time is None:
		log.debug("Couldn't find time")

	message_text = utils.find_message(message.body)
	if message_text is None:
		log.debug("Couldn't find message, defaulting to message link")
		message_text = utils.message_link(message.id)

	reminder = Reminder(
		source=utils.message_link(message.id),
		message=message_text,
		user=message.author.name,
		requested_date=utils.datetime_force_utc(datetime.utcfromtimestamp(message.created_utc)),
		time_string=time
	)
	if not reminder.valid:
		log.debug("Reminder not valid, returning")
		return [reminder.result_message]

	if not database.save_reminder(reminder):
		log.info("Something went wrong saving the reminder")
		return ["Something went wrong saving the reminder"]

	return reminder.render_confirmation()


def process_delete_reminder(message, database):
	return ""


def process_delete_all_reminders(message, database):
	return ""


def process_get_reminders(message, database):
	log.info("Processing get reminders message")

	reminders = database.get_user_reminders(message.author.name)

	bldr = utils.str_bldr()

	if not len(reminders):
		log.debug("User doesn't have any reminders")
		bldr.append("You don't have any reminders.")
	else:
		if len(reminders) > 1:
			bldr.append("[Click here to delete all your reminders](")
			bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove All", "RemoveAll!"))
			bldr.append(")\n\n")

		log.debug(f"Building list with {len(reminders)} reminders")
		bldr.append("|Source|Message|Date|Remove|\n")
		bldr.append("|-|-|-|:-:|\n")
		for reminder in reminders:
			bldr.append("|")
			bldr.append(reminder.source)
			bldr.append("|")
			bldr.append(reminder.message)
			bldr.append("|")
			bldr.append(utils.render_time(reminder.target_date))
			bldr.append("|")
			bldr.append("[Remove](")
			bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove", f"Remove! {reminder.db_id}"))
			bldr.append(")")
			bldr.append("|\n")

			if utils.bldr_length(bldr) > 9000:
				log.debug("Message length too long, returning early")
				bldr.append("\nToo many reminders to display.")
				break

	return bldr


def process_message(message, reddit, database):
	log.info(f"Message /u/{message.author.name} : {message.id}")
	body = message.body.lower()

	bldr = None
	if "remindme" in body:
		bldr = process_remind_me(message, database)
	elif "myreminders!" in body or "!myreminders" in body:
		bldr = process_get_reminders(message, database)

	message.mark_read()

	if bldr is not None:
		bldr.extend(utils.get_footer())
		reddit.reply_message(message, ''.join(bldr))


def process_messages(reddit, database):
	for message in reddit.get_messages():
		#  only process messages here
		process_message(message, reddit, database)
