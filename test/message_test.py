import pytest
from datetime import timedelta
from datetime import datetime

import messages
import utils
import reddit_test
from classes.reminder import Reminder


def assert_date_with_tolerance(source, target, tolerance_minutes):
	assert target - timedelta(minutes=tolerance_minutes) < source < target + timedelta(minutes=tolerance_minutes)


def test_add_reminder(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	keyword = "reminderstring"
	id = utils.random_id()
	message = reddit_test.RedditObject(
		body=f"[{keyword}]\nRemindMe! 1 day",
		author=username,
		created=created,
		id=id
	)

	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "reminderstring" in result

	assert "This time has already passed" not in result
	assert "Could not find a time in message" not in result
	assert "Could not parse date" not in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message == keyword
	assert reminders[0].source == utils.message_link(id)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].db_id is not None


def test_get_reminders(database, reddit):
	message = reddit_test.RedditObject(
		body="MyReminders!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	result = message.get_first_child().body
	assert "You don't have any reminders." in result

	reminder1 = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-01-01 04:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-01-04 05:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-02-02 06:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-02-05 07:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	database.save_reminder(reminder1)
	database.save_reminder(reminder2)

	message = reddit_test.RedditObject(
		body="MyReminders!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "Click here to delete all your reminders" in result

	assert reminder1.source in result
	assert reminder1.message in result
	assert "01-04 05" in result

	assert reminder2.source in result
	assert reminder2.message in result
	assert "02-05 07" in result


def test_delete_reminder(database, reddit):
	reminder1 = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-01-01 04:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-01-04 05:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-02-02 06:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-02-05 07:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	reminder3 = Reminder(
		source="https://www.reddit.com/message/messages/ZZZZZ",
		message="JJJJJ",
		user="Watchful2",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-03-02 06:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-03-05 07:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	database.save_reminder(reminder1)
	database.save_reminder(reminder2)
	database.save_reminder(reminder3)

	message = reddit_test.RedditObject(
		body=f"Remove! test",
		author="Watchful2"
	)
	messages.process_message(message, reddit, database)
	assert "I couldn't find a reminder id to remove." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Remove! {reminder1.db_id}",
		author="Watchful2"
	)
	messages.process_message(message, reddit, database)
	assert "It looks like you don't own this reminder or it doesn't exist." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Remove! {reminder1.db_id}",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Reminder deleted." in message.get_first_child().body

	assert len(database.get_user_reminders("Watchful1")) == 1
	assert len(database.get_user_reminders("Watchful2")) == 1


def test_delete_all_reminders(database, reddit):
	message = reddit_test.RedditObject(
		body=f"RemoveAll!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Deleted" not in message.get_first_child().body

	reminder1 = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-01-01 04:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-01-04 05:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-02-02 06:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-02-05 07:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	reminder3 = Reminder(
		source="https://www.reddit.com/message/messages/ZZZZZ",
		message="JJJJJ",
		user="Watchful2",
		requested_date=utils.datetime_force_utc(datetime.strptime("2019-03-02 06:00:00 AM", '%Y-%m-%d %I:%M:%S %p')),
		target_date=utils.datetime_force_utc(datetime.strptime("2019-03-05 07:00:00 AM", '%Y-%m-%d %I:%M:%S %p'))
	)
	database.save_reminder(reminder1)
	database.save_reminder(reminder2)
	database.save_reminder(reminder3)

	message = reddit_test.RedditObject(
		body=f"RemoveAll!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Deleted **2** reminders." in message.get_first_child().body

	assert len(database.get_user_reminders("Watchful1")) == 0
	assert len(database.get_user_reminders("Watchful2")) == 1
