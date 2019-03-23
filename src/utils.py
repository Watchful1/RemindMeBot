import re
import logging
import dateparser
import pytz
from datetime import datetime


log = logging.getLogger("bot")


def fullname_type(fullname):
	if fullname.startswith("t1"):
		return "comment"
	elif fullname.startswith("t4"):
		return "message"
	else:
		return None


def find_message(body):
	messages = re.findall(r'(?:\[)(.*?)(?:\])', body, flags=re.IGNORECASE)
	if len(messages) > 0:
		return messages[0]
	else:
		return None


def find_time(body):
	times = re.findall(r'(?:remindme.? )(.*)(?:\[|\n|$)', body, flags=re.IGNORECASE)
	if len(times) > 0:
		return times[0]
	else:
		return None


def parse_time(time_string):
	date_time = dateparser.parse(time_string, settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": datetime.utcnow()})
	if date_time.tzinfo is None:
		date_time = datetime_force_utc(date_time)
	return date_time


def render_time(date_time):
	bldr = []
	bldr.append("[**")
	bldr.append(date_time.strftime('%Y-%m-%d %I:%M:%S %p %Z'))
	bldr.append("**](http://www.wolframalpha.com/input/?i=")
	bldr.append(date_time.strftime('%Y-%m-%d %I:%M:%S %p %Z').replace(" ", "%20"))
	bldr.append(" To Local Time".replace(" ", "%20"))
	bldr.append(")")
	return ''.join(bldr)


def message_link(message_id):
	return f"https://www.reddit.com/message/messages/{message_id}"


def datetime_as_utc(date_time):
	return date_time.astimezone(pytz.utc)


def datetime_force_utc(date_time):
	return pytz.utc.localize(date_time)


def datetime_now():
	return datetime_force_utc(datetime.utcnow())
