import utils
import notifications
import static
from database import Database
from praw_wrapper import reddit_test
import messages
from datetime import timedelta
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


def test_send_recurring_reminder_limit(database, reddit):
	old_limit = static.RECURRING_LIMIT
	static.RECURRING_LIMIT = 3
	reminder = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user=database.get_or_add_user("Watchful1"),
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-05 05:00:00"),
		recurrence="one day"
	)
	database.add_reminder(reminder)

	utils.debug_time = utils.parse_datetime_string("2019-01-04 12:00:00")
	for i in range(static.RECURRING_LIMIT + 1):
		utils.debug_time = utils.debug_time + timedelta(days=1)
		notifications.send_reminders(reddit, database)
		assert "I've sent you at least" not in reddit.sent_messages[-1].body
		assert i+1 == database.get_or_add_user("Watchful1").recurring_sent

	utils.debug_time = utils.debug_time + timedelta(days=1)
	notifications.send_reminders(reddit, database)
	assert "I've sent you at least" in reddit.sent_messages[-1].body
	reminders = database.get_all_user_reminders("Watchful1")
	assert len(reminders) == 0

	static.RECURRING_LIMIT = old_limit


def test_reset_recurring_reminder_limit(database, reddit):
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
	assert database.get_or_add_user("Watchful1").recurring_sent == 1

	message = reddit_test.RedditObject(
		body="MyReminders!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)

	assert database.get_or_add_user("Watchful1").recurring_sent == 0


def test_confirm_recurring_reminders(database, reddit):
	cases = [
		{"start": "2019-01-01 04:00:00", "timeString": "1 hour", "targets": ["2019-01-01 05:00:00", "2019-01-01 06:00:00", "2019-01-01 07:00:00"]},
		{"start": "2019-01-01 04:00:00", "timeString": "1 day", "targets": ["2019-01-02 04:00:00", "2019-01-03 04:00:00", "2019-01-04 04:00:00"]},
		{"start": "2019-01-01 04:00:00", "timeString": "4 pm", "targets": ["2019-01-01 16:00:00", "2019-01-02 16:00:00", "2019-01-03 16:00:00"]},
		{"start": "2019-01-01 04:00:00", "timeString": "Monday", "targets": ["2019-01-07 00:00:00", "2019-01-14 00:00:00", "2019-01-21 00:00:00"]},
		{"start": "2019-01-01 04:00:00", "timeString": "1st of the month", "targets": ["2019-02-01 00:00:00", "2019-03-01 00:00:00", "2019-04-01 00:00:00"]},
		{"start": "2019-01-01 04:00:00", "timeString": "October 7th", "targets": ["2019-10-07 00:00:00", "2020-10-07 00:00:00", "2021-10-07 00:00:00"]},
		{"start": "2019-01-01 16:34:41", "timeString": "4:35pm", "targets": ["2019-01-01 16:35:00", "2019-01-02 16:35:00", "2019-01-03 16:35:00"]},
	]

	for case in cases:
		database = Database(debug=True, publish=True)
		reddit = reddit_test.Reddit("Watchful1BotTest")

		# add the reminder
		utils.debug_time = utils.parse_datetime_string(case["start"])
		created = utils.datetime_now()
		username = "Watchful1"
		message = reddit_test.RedditObject(
			body=f"[XXXXX]\n{static.TRIGGER_RECURRING}! {case['timeString']}",
			author="Watchful1",
			created=created,
			id=reddit_test.random_id()
		)
		messages.process_message(message, reddit, database)

		# verify it was added correctly
		reminders = database.get_all_user_reminders(username)
		assert len(reminders) == 1
		assert reminders[0].requested_date == created
		assert reminders[0].target_date == utils.parse_datetime_string(case["targets"][0])
		assert reminders[0].recurrence == case["timeString"]

		# send it once and verify the new target time
		utils.debug_time = utils.parse_datetime_string(case["targets"][0]) + timedelta(seconds=1)
		notifications.send_reminders(reddit, database)
		assert len(reddit.sent_messages) == 2
		reminders = database.get_all_user_reminders(username)
		assert len(reminders) == 1
		assert reminders[0].target_date == utils.parse_datetime_string(case["targets"][1])

		# send it again and verify the second target time
		utils.debug_time = utils.parse_datetime_string(case["targets"][1]) + timedelta(seconds=1)
		notifications.send_reminders(reddit, database)
		assert len(reddit.sent_messages) == 3
		reminders = database.get_all_user_reminders(username)
		assert len(reminders) == 1
		assert reminders[0].target_date == utils.parse_datetime_string(case["targets"][2])
