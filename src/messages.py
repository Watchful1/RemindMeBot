import logging
from datetime import datetime

import utils
from classes.reminder import Reminder

log = logging.getLogger("bot")


def process_remind_me(message, database):
	log.info("Processing RemindMe message")
	time = utils.find_time(message.body)
	if time is None:
		log.info("Couldn't find time")

	message_text = utils.find_message(message.body)
	if message_text is None:
		log.info("Couldn't find message, defaulting to message link")
		message_text = utils.message_link(message.id)

	reminder = Reminder(
		source_id=message.fullname,
		message=message_text,
		user=message.author.name,
		requested_date=utils.datetime_force_utc(datetime.utcfromtimestamp(message.created_utc)),
		time_string=time
	)
	if not reminder.valid:
		return reminder.result_message

	if not database.save_reminder(reminder):
		return "Something went wrong saving the reminder"

	return reminder.render_confirmation()


def process_messages(reddit, database):
	for message in reddit.get_messages():
		log.info(f"Message /u/{message.author.name} : {message.id}")
		body = message.body.lower()
		result_message = None
		if "remindme" in body:
			result_message = process_remind_me(message, database)

		message.mark_read()

		if result_message is not None:
			message.reply(result_message)
