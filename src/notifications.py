import discord_logging
import re

import utils
import static
import counters
from datetime import timedelta
from praw_wrapper.reddit import ReturnType


log = discord_logging.get_logger()


def send_reminders(reddit, database):
	timestamp = utils.datetime_now()
	count_reminders = database.get_count_pending_reminders(timestamp)
	counters.queue.set(count_reminders)

	reminders_sent = 0
	if count_reminders > 0:
		reminders = database.get_pending_reminders(utils.requests_available(count_reminders), timestamp)
		for reminder in reminders:
			reminders_sent += 1
			counters.notifications.inc()
			counters.queue.dec()
			if re.search(r"[^\w_-]", reminder.user.name):
				log.warning(f"Can't send reminder, invalid username: u/{reminder.user.name} : {reminder.id} : {utils.get_datetime_string(reminder.target_date)}")
				log.debug(f"{reminder.id} deleted")
				database.delete_reminder(reminder)

			else:
				log.info(
					f"{reminders_sent}/{len(reminders)}/{count_reminders}: Sending reminder to u/{reminder.user.name} : "
					f"{reminder.id} : {utils.get_datetime_string(reminder.target_date)}")
				bldr = utils.get_footer(reminder.render_notification())
				result = reddit.send_message(reminder.user.name, "RemindMeBot Here!", ''.join(bldr), retry_seconds=60)
				if result in [ReturnType.INVALID_USER, ReturnType.USER_DOESNT_EXIST]:
					log.info(f"User doesn't exist: u/{reminder.user.name}")
				elif result in [ReturnType.NOT_WHITELISTED_BY_USER_MESSAGE]:
					log.info(f"User blocked notification message: u/{reminder.user.name}")
				elif result in [ReturnType.SERVER_ERROR]:
					log.warning(f"Server error sending notification message to u/{reminder.user.name}")
					counters.errors.labels(type='api').inc()

				if reminder.recurrence is not None:
					if reminder.user.recurring_sent > static.RECURRING_LIMIT:
						log.info(f"User u/{reminder.user.name} hit their recurring limit, deleting reminder {reminder.id}")
						database.delete_reminder(reminder)
					else:
						new_target_date = utils.next_recurring_time(reminder.recurrence, reminder.target_date, reminder.user.timezone)
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
