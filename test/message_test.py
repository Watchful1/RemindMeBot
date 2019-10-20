from datetime import timedelta
import pytz
import discord_logging

log = discord_logging.get_logger(init=True)

import messages
import utils
import reddit_test
import static
from database import Database
from classes.reminder import Reminder
from classes.comment import DbComment
from classes.cakeday import Cakeday
from classes.user_settings import UserSettings


def test_sandbox():
	database = Database()

	reminder = Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message="KKKKK",
		user="Watchful1",
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-04 05:00:00")
	)

	log.info(reminder.id)

	database.add_reminder(reminder)

	database.commit()

	log.info(reminder.id)


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
	assert reminders[0].id is not None


def test_add_cakeday(database, reddit):
	username = "Watchful1"
	created = utils.parse_datetime_string("2015-05-05 15:25:17")
	user = reddit_test.User(username, created.timestamp())
	message = reddit_test.RedditObject(
		body="Cakeday!",
		author=user
	)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "to remind you of your cakeday" in result

	cakeday = database.get_cakeday(username)
	assert cakeday is not None
	assert cakeday.user == username
	assert cakeday.date_time == utils.parse_datetime_string("2019-05-05 15:25:17")
	assert cakeday.db_id is not None


def test_add_cakeday_exists(database, reddit):
	username = "Watchful1"
	created = utils.parse_datetime_string("2015-05-05 15:25:17")
	user = reddit_test.User(username, created.timestamp())
	message = reddit_test.RedditObject(
		body="Cakeday!",
		author=user
	)
	messages.process_message(message, reddit, database)

	message2 = reddit_test.RedditObject(
		body="Cakeday!",
		author=user
	)
	messages.process_message(message2, reddit, database)

	result = message2.get_first_child().body

	assert "It looks like you already have a cakeday reminder set." in result


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
	assert reminders[0].id is not None


def test_add_reminder_no_date(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	id = utils.random_id()
	message = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! \"error test\"",
		author=username,
		created=created,
		id=id
	)

	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "This time has already passed" not in result
	assert "Could not find a time in message, defaulting to one day" in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message == "error test"
	assert reminders[0].source == utils.message_link(id)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None


def test_get_reminders(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-01 12:00:00")
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
	cakeday = Cakeday(
		user="Watchful1",
		date_time=utils.parse_datetime_string("2019-05-05 15:25:17")
	)
	database.add_cakeday(cakeday)

	message = reddit_test.RedditObject(
		body="MyReminders!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	result = message.get_first_child().body

	assert "Click here to delete all your reminders" in result

	assert "Happy cakeday!" in result

	assert reminder1.source in result
	assert reminder1.message in result
	assert "01-04 05" in result

	assert reminder2.source in result
	assert reminder2.message in result
	assert "02-05 07" in result

	database.save_settings(
		UserSettings(
			user="Watchful1",
			timezone="America/Los_Angeles"
		)
	)
	messages.process_message(message, reddit, database)
	result = message.get_last_child().body
	assert "Your timezone is currently set to: `America/Los_Angeles`" in result
	assert "01-03 21" in result
	assert "02-04 23" in result


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
		body=f"Remove! {reminder1.id}",
		author="Watchful2"
	)
	messages.process_message(message, reddit, database)
	assert "It looks like you don't own this reminder or it doesn't exist." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Remove! {reminder1.id}",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Reminder deleted." in message.get_first_child().body

	assert len(database.get_user_reminders("Watchful1")) == 1
	assert len(database.get_user_reminders("Watchful2")) == 1


def test_remove_cakeday(database, reddit):
	cakeday1 = Cakeday(
		user="Watchful1",
		date_time=utils.parse_datetime_string("2015-05-05 15:25:17")
	)
	cakeday2 = Cakeday(
		user="Watchful2",
		date_time=utils.parse_datetime_string("2015-05-05 15:25:17")
	)
	database.add_cakeday(cakeday1)
	database.add_cakeday(cakeday2)

	message = reddit_test.RedditObject(
		body=f"Remove! cakeday",
		author="Watchful3"
	)
	messages.process_message(message, reddit, database)
	assert "You don't have a cakeday reminder set." in message.get_first_child().body

	message = reddit_test.RedditObject(
		body=f"Remove! cakeday",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	assert "Cakeday reminder deleted." in message.get_first_child().body
	assert database.get_cakeday("Watchful1") is None
	assert database.get_cakeday("Watchful2") is not None


def test_remove_all_reminders(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-01 12:00:00")
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
	cakeday = Cakeday(
		user="Watchful1",
		date_time=utils.parse_datetime_string("2019-05-05 15:25:17")
	)
	database.add_cakeday(cakeday)

	message = reddit_test.RedditObject(
		body=f"RemoveAll!",
		author="Watchful1"
	)
	messages.process_message(message, reddit, database)
	body = message.get_first_child().body
	assert "Deleted **2** reminders." in body
	assert "Deleted cakeday reminder." in body

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
		id="ZZZZZ"
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
	assert comment.id not in reddit.all_comments


def test_set_timezone(database, reddit):
	username = "Watchful1"
	message = reddit_test.RedditObject(
		body="Timezone! ",
		author=username
	)
	messages.process_message(message, reddit, database)
	result = message.get_last_child().body
	assert "I couldn't find a timezone in your message." in result

	message.body = "Timezone! EST"
	messages.process_message(message, reddit, database)
	result = message.get_last_child().body
	assert "EST is not a valid timezone." in result

	message.body = "Timezone! America/Los_Angeles"
	messages.process_message(message, reddit, database)
	result = message.get_last_child().body
	assert "Updated your timezone to America/Los_Angeles" in result
	user_settings = database.get_settings(username)
	assert user_settings.timezone == "America/Los_Angeles"

	message.body = "Timezone! UTC"
	messages.process_message(message, reddit, database)
	result = message.get_last_child().body
	assert "Reset your timezone to the default" in result
	user_settings = database.get_settings(username)
	assert user_settings.timezone is None


def test_timezone_reminder_message(database, reddit):
	timezone_string = "America/Los_Angeles"
	database.save_settings(
		UserSettings(
			user="Watchful1",
			timezone=timezone_string
		)
	)

	created = utils.datetime_now()
	target = created + timedelta(hours=24)
	username = "Watchful1"
	message = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! {utils.get_datetime_string(utils.datetime_as_timezone(target, timezone_string))}",
		author=username,
		created=created
	)

	messages.process_message(message, reddit, database)

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == utils.datetime_as_utc(
		pytz.timezone(timezone_string).localize(target.replace(tzinfo=None))
	)
