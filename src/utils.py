import re
import logging
import dateparser
from datetime import datetime

from classes import Reminder


log = logging.getLogger("bot")


def fullname_type(fullname):
	if fullname.startswith("t1"):
		return "comment"
	elif fullname.startswith("t4"):
		return "message"
	else:
		return None


def find_message(body):
	messages = re.findall(r'(?:\[)(.*?)(?:\])', body)
	if len(messages) > 0:
		return messages[0]
	else:
		return None


def find_time(body):
	times = re.findall(r'(?:remindme.? )(.*)(?:\[|\n|$)', body)
	if len(times) > 0:
		return times[0]
	else:
		return None


def parse_time(time_string):
	return dateparser.parse(time_string, settings={"PREFER_DATES_FROM": 'future'})


def build_reminder(time_string, message, source_id, user):
	if time_string is None:
		target_date = None
	else:
		target_date = parse_time(time_string)

	result_string = None
	if target_date is None:
		if time_string is None:
			result_string = "Could not find a time in message, defaulting to one day"
		else:
			result_string = f"Could not parse date: {time_string}, defaulting to one day"
		log.warning(result_string)
		target_date = parse_time("1 day")

	if target_date < datetime.utcnow():
		result_string = f"This time has already passed: {time_string}"
		log.warning(result_string)
		return None, result_string

	return Reminder(source_id, target_date, message, user), result_string
