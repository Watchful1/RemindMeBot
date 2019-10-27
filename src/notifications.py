import discord_logging

import utils
from classes.enums import ReturnType


log = discord_logging.get_logger()


def send_reminders(reddit, database):
	timestamp = utils.datetime_now()
	count_reminders = database.get_count_pending_reminders(timestamp)

	reminders = database.get_pending_reminders(utils.requests_available(count_reminders), timestamp)
	if len(reminders) > 0:
		i = 0
		for reminder in reminders:
			i += 1
			log.info(
				f"{i}/{len(reminders)}/{count_reminders}: Sending reminder to u/{reminder.user.name} : "
				f"{reminder.id} : {utils.get_datetime_string(reminder.target_date)}")
			bldr = utils.get_footer(reminder.render_notification())
			result = reddit.send_message(reminder.user.name, "RemindMeBot Here!", ''.join(bldr))
			if result in (ReturnType.INVALID_USER, ReturnType.USER_DOESNT_EXIST):
				log.info(f"User doesn't exist: u/{reminder.user.name}")

			database.delete_reminder(reminder)

	else:
		log.debug("No reminders to send")

	return len(reminders)
