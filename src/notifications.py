import logging.handlers

import utils

log = logging.getLogger("bot")


def send_reminders(reddit, database, timestamp=None):
	if timestamp is None:
		timestamp = utils.datetime_now()
	count_reminders = database.get_count_pending_reminders(timestamp)
	if count_reminders == 0:
		count_to_send = 0
	elif count_reminders < 200:
		count_to_send = 30
	else:
		count_to_send = min(1000, int(count_reminders / 5))

	reminders = database.get_pending_reminders(count_to_send, timestamp)
	if len(reminders) > 0:
		i = 0
		for reminder in reminders:
			i += 1
			log.info(
				f"{i}/{len(reminders)}/{count_reminders}: Sending reminder to u/{reminder.user} : "
				f"{reminder.db_id} : {utils.get_datetime_string(reminder.target_date)}")
			bldr = utils.get_footer(reminder.render_notification())
			reddit.send_message(reminder.user, "RemindMeBot Here!", ''.join(bldr))

			database.delete_reminder(reminder)

	else:
		log.debug("No reminders to send")
