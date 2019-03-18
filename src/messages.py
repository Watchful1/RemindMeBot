import logging

from classes import Reminder
import utils
import database

log = logging.getLogger("bot")


def process_remind_me(message):
	log.info("Processing RemindMe message")
	time = utils.find_time(message.body)
	if time is None:
		log.info("Couldn't find time")

	message_text = utils.find_message(message.body)
	if message_text is None:
		log.info("Couldn't find message")
		return "I couldn't find anything to remind you of. Put the link to the post or a comment describing your " \
			"reminder in square brackets []"

	reminder, result_string = utils.build_reminder(time, message_text, message.fullname, message.author.name)
	if reminder is None:
		log.info("Error building reminder: {}".format(reminder.error))
		return reminder.error

	success = database.save_reminder(reminder)
	if not success:
		log.warning("Failed to save reminder")
		return "Something went wrong"


def process_messages(reddit):
	for message in reddit.get_messages():
		log.info("Message /u/{}".format(message.author.name))
		body = message.body.lower()
		if "remindme" in body:
			result_message = process_remind_me(message)
