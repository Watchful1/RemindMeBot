from datetime import timedelta
from datetime import datetime

import messages
import utils
import reddit_test
import static
from classes.reminder import Reminder
from classes.comment import DbComment


def assert_date_with_tolerance(source, target, tolerance_minutes):
	assert target - timedelta(minutes=tolerance_minutes) < source < target + timedelta(minutes=tolerance_minutes)


def test_add_reminder(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	keyword = "reminderstring"
	id = utils.random_id()
	message = reddit_test.RedditObject(
		body=f"[{keyword}]\n{static.TRIGGER}! 1 day",
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


def test_add_reminder_no_message(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	id = utils.random_id()
	message = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author=username,
		created=created,
		id=id
	)

	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "This time has already passed" not in result
	assert "Could not find a time in message" not in result
	assert "Could not parse date" not in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.message_link(id)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].db_id is not None


def test_add_reminder_no_message(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	id = utils.random_id()
	message = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author=username,
		created=created,
		id=id
	)

	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "This time has already passed" not in result
	assert "Could not find a time in message" not in result
	assert "Could not parse date" not in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message is None
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
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-04 05:00:00")
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.parse_datetime_string("2019-02-02 06:00:00"),
		target_date=utils.parse_datetime_string("2019-02-05 07:00:00")
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


def test_remove_reminder(database, reddit):
	reminder1 = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user="Watchful1",
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-04 05:00:00")
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.parse_datetime_string("2019-02-02 06:00:00"),
		target_date=utils.parse_datetime_string("2019-02-05 07:00:00")
	)
	reminder3 = Reminder(
		source="https://www.reddit.com/message/messages/ZZZZZ",
		message="JJJJJ",
		user="Watchful2",
		requested_date=utils.parse_datetime_string("2019-03-02 06:00:00"),
		target_date=utils.parse_datetime_string("2019-03-05 07:00:00")
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


def test_remove_all_reminders(database, reddit):
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
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-04 05:00:00")
	)
	reminder2 = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="FFFFF",
		user="Watchful1",
		requested_date=utils.parse_datetime_string("2019-02-02 06:00:00"),
		target_date=utils.parse_datetime_string("2019-02-05 07:00:00")
	)
	reminder3 = Reminder(
		source="https://www.reddit.com/message/messages/ZZZZZ",
		message="JJJJJ",
		user="Watchful2",
		requested_date=utils.parse_datetime_string("2019-03-02 06:00:00"),
		target_date=utils.parse_datetime_string("2019-03-05 07:00:00")
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


def test_delete_comment(database, reddit):
	db_comment = DbComment(
		thread_id="XXXXX",
		comment_id="ZZZZZ",
		reminder_id="YYYYY",
		user="Watchful1",
		source="www.reddit.com/r/test/comments/XXXXX",
		current_count=1
	)
	database.save_comment(db_comment)
	comment = reddit_test.RedditObject(
		body="Click here for a reminder!",
		author=static.ACCOUNT_NAME,
		id="YYYYY"
	)
	reddit.add_comment(comment, True)

	message = reddit_test.RedditObject(
		body=f"Delete! SSSSSS",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "This comment doesn't exist or was already deleted." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Delete! XXXXX",
		author="Watchful2"
	)
	messages.process_message(message, reddit, database)
	assert "It looks like the bot wasn't replying to you." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Delete! XXXXX",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Comment deleted." in message.get_first_child().body
