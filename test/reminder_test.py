import utils
import notifications
from classes.reminder import Reminder


def test_send_reminder(database, reddit):
	reminder = Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		)
	database.add_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(reddit.sent_messages) == 1

	message_body = reddit.sent_messages[0].body
	assert "I'm here to remind you" in message_body
	assert reminder.message in message_body
	assert "The source comment or message" in message_body
	assert reminder.source in message_body

	reminders = database.get_all_user_reminders("Watchful1")
	assert len(reminders) == 0


def test_send_reminders(database, reddit):
	reminders = [
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-06 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-08 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.add_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(database.get_all_user_reminders("Watchful1")) == 4

	utils.debug_time = utils.parse_datetime_string("2019-01-08 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(database.get_all_user_reminders("Watchful1")) == 1


def test_send_recurring_reminder(database, reddit):
	reminder = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user=database.get_or_add_user("Watchful1"),
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-05 05:00:00"),
		recurrence="one day"
	)
	database.add_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(reddit.sent_messages) == 1

	message_body = reddit.sent_messages[0].body
	assert "I'm here to remind you" in message_body
	assert reminder.message in message_body
	assert "The source comment or message" in message_body
	assert reminder.source in message_body
	assert "This is a repeating reminder. I'll message you again in " in message_body
	assert reminder.recurrence in message_body

	reminders = database.get_all_user_reminders("Watchful1")
	assert len(reminders) == 1
	assert reminders[0].target_date == utils.parse_datetime_string("2019-01-06 05:00:00")
