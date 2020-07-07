import discord_logging

import utils
import static
from praw_wrapper import ReturnType


log = discord_logging.get_logger()


def send_reminders(reddit, database, counters=None):
	timestamp = utils.datetime_now()
	count_reminders = database.get_count_pending_reminders(timestamp)
	if counters is not None:
		counters.queue_size.set(count_reminders)

	reminders_sent = 0
	if count_reminders > 0:
		reminders = database.get_pending_reminders(utils.requests_available(count_reminders), timestamp)
		for reminder in reminders:
			reminders_sent += 1
			if counters is not None:
				counters.notifications_sent.inc()
				counters.queue_size.dec()
			log.info(
				f"{reminders_sent}/{len(reminders)}/{count_reminders}: Sending reminder to u/{reminder.user.name} : "
				f"{reminder.id} : {utils.get_datetime_string(reminder.target_date)}")
			bldr = utils.get_footer(reminder.render_notification())
			result = reddit.send_message(reminder.user.name, "RemindMeBot Here!", ''.join(bldr))
			if result in [ReturnType.INVALID_USER, ReturnType.USER_DOESNT_EXIST]:
				log.info(f"User doesn't exist: u/{reminder.user.name}")
			if result in [ReturnType.NOT_WHITELISTED_BY_USER_MESSAGE]:
				log.info(f"User blocked notification message: u/{reminder.user.name}")

			if reminder.recurrence is not None:
				if reminder.user.recurring_sent > static.RECURRING_LIMIT:
					log.info(f"User u/{reminder.user.name} hit their recurring limit, deleting reminder {reminder.id}")
					database.delete_reminder(reminder)
				else:
					new_target_date = utils.parse_time(reminder.recurrence, reminder.target_date, reminder.user.timezone)
					log.info(f"{reminder.id} recurring from {utils.get_datetime_string(reminder.target_date)} to "
							 f"{utils.get_datetime_string(new_target_date)}")
					reminder.target_date = new_target_date
					reminder.user.recurring_sent += 1
			else:
				log.debug(f"{reminder.id} deleted")
				database.delete_reminder(reminder)

		database.commit()

	else:
		log.debug("No reminders to send")

	return reminders_sent
