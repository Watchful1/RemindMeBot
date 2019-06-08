import utils
import notifications
from classes.reminder import Reminder
from classes.cakeday import Cakeday


def test_send_reminder(database, reddit):
	reminder = Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		)
	database.save_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(reddit.sent_messages) == 1

	message_body = reddit.sent_messages[0].body
	assert "I'm here to remind you" in message_body
	assert reminder.message in message_body
	assert "The source comment or message" in message_body
	assert reminder.source in message_body


def test_send_reminders(database, reddit):
	reminders = [
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-06 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-08 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="KKKKK",
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.save_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(database.get_user_reminders("Watchful1")) == 4

	utils.debug_time = utils.parse_datetime_string("2019-01-08 12:00:00")
	notifications.send_reminders(reddit, database)

	assert len(database.get_user_reminders("Watchful1")) == 1


def test_send_cakedays(database, reddit):
	cakedays = [
		Cakeday(
			user="Watchful1",
			date_time=utils.parse_datetime_string("2019-01-01 04:00:00")
		),
		Cakeday(
			user="Watchful2",
			date_time=utils.parse_datetime_string("2019-01-02 04:00:00")
		),
		Cakeday(
			user="Watchful3",
			date_time=utils.parse_datetime_string("2019-01-03 04:00:00")
		),
		Cakeday(
			user="Watchful4",
			date_time=utils.parse_datetime_string("2019-01-04 04:00:00")
		)
	]
	for cakeday in cakedays:
		database.add_cakeday(cakeday)

	utils.debug_time = utils.parse_datetime_string("2019-01-01 02:00:00")
	notifications.send_cakeday_notifications(reddit, database)
	assert len(reddit.sent_messages) == 0

	utils.debug_time = utils.parse_datetime_string("2019-01-01 06:00:00")
	notifications.send_cakeday_notifications(reddit, database)
	assert len(reddit.sent_messages) == 1
	assert database.get_cakeday("Watchful1").date_time == utils.parse_datetime_string("2020-01-01 04:00:00")

	utils.debug_time = utils.parse_datetime_string("2019-01-03 06:00:00")
	notifications.send_cakeday_notifications(reddit, database)
	assert len(reddit.sent_messages) == 3
	assert database.get_cakeday("Watchful1").date_time == utils.parse_datetime_string("2020-01-01 04:00:00")
	assert database.get_cakeday("Watchful2").date_time == utils.parse_datetime_string("2020-01-02 04:00:00")
	assert database.get_cakeday("Watchful4").date_time == utils.parse_datetime_string("2019-01-04 04:00:00")
