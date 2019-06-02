import logging
import re
import traceback

import utils
import static
from classes.reminder import Reminder

log = logging.getLogger("bot")


def get_reminders_string(user, database, previous=False):
	bldr = utils.str_bldr()

	reminders = database.get_user_reminders(user)
	if len(reminders):
		if previous:
			bldr.append("Your previous reminders:")
		else:
			bldr.append("Your current reminders:")
		bldr.append("\n\n")

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
	else:
		bldr.append("You don't have any reminders.")

	return bldr


def process_remind_me(message, database):
	log.info("Processing RemindMe message")
	time = utils.find_reminder_time(message.body)

	message_text = utils.find_reminder_message(message.body)

	reminder = Reminder(
		source=utils.message_link(message.id),
		message=message_text,
		user=message.author.name,
		requested_date=utils.datetime_from_timestamp(message.created_utc),
		time_string=time
	)
	if not reminder.valid:
		log.debug("Reminder not valid, returning")
		return [reminder.result_message]

	if not database.save_reminder(reminder):
		log.info("Something went wrong saving the reminder")
		return ["Something went wrong saving the reminder"]

	log.info(f"Reminder created: {reminder.db_id} : {utils.get_datetime_string(reminder.target_date)}")

	return reminder.render_message_confirmation()


def process_remove_reminder(message, database):
	log.info("Processing remove reminder message")
	bldr = utils.str_bldr()

	ids = re.findall(r'remove!\s(\d+)', message.body, flags=re.IGNORECASE)
	if len(ids) == 0:
		bldr.append("I couldn't find a reminder id to remove.")
	else:
		reminder = database.get_reminder(ids[0])
		if reminder is None or reminder.user != message.author.name:
			bldr.append("It looks like you don't own this reminder or it doesn't exist.")
		else:
			if database.delete_reminder(reminder):
				bldr.append("Reminder deleted.")
			else:
				bldr.append("Something went wrong, reminder not deleted.")

	bldr.append(" ")

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
				comment = reddit.get_comment(ids[0])
				if not reddit.delete_comment(comment) or not database.delete_comment(db_comment):
					log.debug(f"Unable to delete comment: {ids[0]}")
					bldr.append("Something went wrong deleting the comment")
				else:
					log.debug(f"Deleted comment: {ids[0]}")
					bldr.append("Comment deleted.")
			else:
				log.debug(f"Bot wasn't replying to owner: {db_comment.user} : {message.author.name}")
				bldr.append("It looks like the bot wasn't replying to you.")
		else:
			log.debug(f"Comment doesn't exist: {ids[0]}")
			bldr.append("This comment doesn't exist or was already deleted.")

	return bldr


def process_message(message, reddit, database):
	log.info(f"Message u/{message.author.name} : {message.id}")
	body = message.body.lower()

	bldr = None
	if static.TRIGGER_LOWER in body:
		bldr = process_remind_me(message, database)
	elif "myreminders!" in body:
		bldr = process_get_reminders(message, database)
	elif "remove!" in body:
		bldr = process_remove_reminder(message, database)
	elif "removeall!" in body:
		bldr = process_remove_all_reminders(message, database)
	elif "delete!" in body:
		bldr = process_delete_comment(message, reddit, database)

	if bldr is None:
		bldr = ["I couldn't find anything in your message."]

	bldr.extend(utils.get_footer())
	reddit.reply_message(message, ''.join(bldr))


def process_messages(reddit, database):
	messages = reddit.get_messages()
	if len(messages):
		log.debug(f"Processing {len(messages)} messages")
	for message in messages[::-1]:
		if reddit.is_message(message):
			try:
				process_message(message, reddit, database)
			except Exception:
				log.warning(f"Error processing message: {message.id} : u/{message.author.name}")
				log.warning(traceback.format_exc())
		else:
			log.debug(f"Object not message, skipping: {message.id}")

		try:
			reddit.mark_read(message)
		except Exception:
			log.warning(f"Error marking message read: {message.id} : {message.author.name}")
			log.warning(traceback.format_exc())

