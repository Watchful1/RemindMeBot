import re
import logging
import dateparser
import pytz
from datetime import datetime

import static


log = logging.getLogger("bot")


def fullname_type(fullname):
	if fullname.startswith("t1"):
		return "comment"
	elif fullname.startswith("t4"):
		return "message"
	else:
		return None


def find_reminder_message(body):
	messages = re.findall(r'(?:\[)(.*?)(?:\])', body, flags=re.IGNORECASE)
	if len(messages) > 0:
		return messages[0]
	else:
		return None


def find_reminder_time(body):
	times = re.findall(r'(?:remindme.? )(.*)(?:\[|\n|$)', body, flags=re.IGNORECASE)
	if len(times) > 0:
		return times[0]
	else:
		return None


def parse_time(time_string, base_time=datetime.utcnow()):
	date_time = dateparser.parse(time_string, settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time})
	if date_time.tzinfo is None:
		date_time = datetime_force_utc(date_time)
	return date_time


def render_time(date_time):
	bldr = str_bldr()
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
	return datetime_force_utc(datetime.utcnow().replace(microsecond=0))


def html_encode(message):
	encodings = {
		' ': '%20',
		'(': '%28',
		')': '%29',
		'\n': '%0A'
	}
	return re.sub(r'[ ()\n]', lambda a: encodings[a.group(0)] if a.group(0) in encodings else a.group(0), message)


def build_message_link(recipient, subject, content=None):
	base = "https://np.reddit.com/message/compose/?"
	bldr = str_bldr()
	bldr.append("to=")
	bldr.append(recipient)
	bldr.append("subject=")
	bldr.append(html_encode(subject))
	if content is not None:
		bldr.append(f"message=")
		bldr.append(html_encode(content))

	return base + '&'.join(bldr)


def get_footer():
	bldr = str_bldr()
	bldr.append("\n\n")
	bldr.append("*****")
	bldr.append("\n\n")

	bldr.append("|[^(Info)](http://np.reddit.com/r/RemindMeBot/comments/24duzp/remindmebot_info/)")
	bldr.append("|[^(Custom)]()")
	bldr.append(build_message_link(
		static.ACCOUNT_NAME,
		"Reminder",
		"[Link or message inside square brackets]\n\nRemindMe! Time period here"
	))
	bldr.append(")")
	bldr.append("|[^(Your Reminders)]()")
	bldr.append(build_message_link(
		static.ACCOUNT_NAME,
		"List Of Reminders",
		"MyReminders!"
	))
	bldr.append(")")
	bldr.append("|[^(Feedback)]()")
	bldr.append(build_message_link(
		static.OWNER,
		"Feedback"
	))
	bldr.append(")")
	bldr.append("|\n|-|-|-|-|")

	return bldr


def str_bldr():
	return []


def bldr_length(bldr):
	length = 0
	for item in bldr:
		length += len(item)
	return length
