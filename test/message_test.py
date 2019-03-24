import pytest
import random
from datetime import timedelta
from datetime import datetime

import messages
import utils


def assert_date_with_tolerance(source, target, tolerance_minutes):
	assert target - timedelta(minutes=tolerance_minutes) < source < target + timedelta(minutes=tolerance_minutes)


def random_id():
	values = list(map(chr, range(97, 123)))
	for num in range(1, 10):
		values.append(str(num))
	return ''.join(random.choices(values, k=6))


class TempAuthor:
	def __init__(self, name):
		self.name = name


class TempMessage:
	def __init__(
		self,
		body,
		author,
		created=None,
		source_id=None
	):
		self.body = body
		self.author = TempAuthor(author)
		if source_id is None:
			self.id = random_id()
		else:
			self.id = source_id
		self.fullname = "t4_"+self.id
		if created is None:
			self.created_utc = utils.datetime_now().timestamp()
		else:
			self.created_utc = created.timestamp()


def test_add_reminder(database):
	created = utils.datetime_now()
	username = "Watchful1"
	keyword = "reminderstring"
	source_id = random_id()
	message = TempMessage(
		body=f"[{keyword}]\nRemindMe! 1 day",
		author=username,
		created=created,
		source_id=source_id
	)

	result = messages.process_remind_me(message, database)

	assert "reminderstring" in result

	assert "This time has already passed" not in result
	assert "Could not find a time in message" not in result
	assert "Could not parse date" not in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message == keyword
	assert reminders[0].source_id == "t4_"+source_id
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
