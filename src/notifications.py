import discord_logging

import utils


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
				f"{i}/{len(reminders)}/{count_reminders}: Sending reminder to u/{reminder.user} : "
				f"{reminder.db_id} : {utils.get_datetime_string(reminder.target_date)}")
			bldr = utils.get_footer(reminder.render_notification())
			reddit.send_message(reminder.user, "RemindMeBot Here!", ''.join(bldr))

			database.delete_reminder(reminder)

	else:
		log.debug("No reminders to send")

	return len(reminders)


def send_cakeday_notifications(reddit, database):
	timestamp = utils.datetime_now()
	count_cakedays = database.get_count_pending_cakedays(timestamp)

	cakedays = database.get_pending_cakedays(utils.requests_available(count_cakedays), timestamp)
	if len(cakedays) > 0:
		i = 0
		for cakeday in cakedays:
			i += 1
			log.info(
				f"{i}/{len(cakedays)}/{count_cakedays}: Sending cakeday notification to u/{cakeday.user} : "
				f"{cakeday.db_id} : {utils.get_datetime_string(cakeday.date_time)}")
			bldr = utils.get_footer(cakeday.render_notification())
			reddit.send_message(cakeday.user, "RemindMeBot Here! Happy cakeday!", ''.join(bldr))

			database.bump_cakeday(cakeday)

	else:
		log.debug("No cakedays to send")

	return len(cakedays)
