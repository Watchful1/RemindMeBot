import re
import discord_logging
import dateparser
from dateparser.search import search_dates
import parsedatetime
import pytz
from datetime import datetime
from datetime import timedelta
import urllib.parse

import static
import random

log = discord_logging.get_logger()
debug_time = None
cal = parsedatetime.Calendar()


def random_id():
	values = list(map(chr, range(97, 123)))
	for num in range(1, 10):
		values.append(str(num))
	return ''.join(random.choices(values, k=6))


def fullname_type(fullname):
	if fullname.startswith("t1"):
		return "comment"
	elif fullname.startswith("t4"):
		return "message"
	else:
		return None


def find_reminder_message(body):
	line_messages = re.findall(
		r'(?:{trigger}.*[\[\"“])(.*?)(?:[\]\"”])(?:[^(]|\n|$)'.format(trigger=static.TRIGGER_LOWER),
		body,
		flags=re.IGNORECASE)
	if len(line_messages) > 0:
		return line_messages[0]

	messages = re.findall(r'(?:[\[\"“])(.*?)(?:[\]\"”])(?:[^(]|\n|$)', body, flags=re.IGNORECASE)
	if len(messages) > 0:
		return messages[0]
	else:
		return None


def find_reminder_time(body):
	regex_string = r'(?:{trigger}.? )(.*?)(?:\[|\n|\"|$)'.format(trigger=static.TRIGGER_LOWER)
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0]
	else:
		return None


def parse_time(time_string, base_time, timezone_string):
	if timezone_string is not None:
		base_time = base_time.astimezone(pytz.timezone(timezone_string))

	try:
		date_time = dateparser.parse(
			time_string,
			settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
	except Exception:
		date_time = None

	if date_time is None:
		try:
			date_time, result_code = cal.parseDT(time_string, base_time)
			if result_code == 0:
				date_time = None
		except Exception:
			date_time = None

	if date_time is None:
		return None

	if date_time.tzinfo is None:
		if timezone_string is not None:
			date_time = pytz.timezone(timezone_string).localize(date_time)
		else:
			date_time = datetime_force_utc(date_time)

	if date_time.tzinfo != pytz.utc:
		date_time = date_time.astimezone(pytz.utc)

	return date_time


def render_time(date_time, timezone=None, format_string="%Y-%m-%d %H:%M:%S %Z"):
	bldr = str_bldr()
	bldr.append("[**")
	bldr.append(datetime_as_timezone(date_time, timezone).strftime(format_string))
	bldr.append("**](http://www.wolframalpha.com/input/?i=")
	bldr.append(date_time.strftime('%Y-%m-%d %H:%M:%S %Z').replace(" ", "%20"))
	bldr.append(" To Local Time".replace(" ", "%20"))
	bldr.append(")")
	return ''.join(bldr)


def message_link(message_id, np=False):
	return f"https://{('np' if np else 'www')}.reddit.com/message/messages/{message_id}"


def reddit_link(slug, np=False):
	return f"https://{('np' if np else 'www')}.reddit.com{slug}"


def id_from_fullname(fullname):
	return re.sub(r't\d_', "", fullname)


def datetime_as_timezone(date_time, timezone_string):
	if timezone_string is None:
		return date_time
	else:
		return date_time.astimezone(pytz.timezone(timezone_string))


def datetime_as_utc(date_time):
	return date_time.astimezone(pytz.utc)


def datetime_force_utc(date_time):
	return pytz.utc.localize(date_time)


def time_offset(date_time, hours=0, minutes=0, seconds=0):
	if date_time is None:
		return True
	return date_time < datetime_now() - timedelta(hours=hours, minutes=minutes, seconds=seconds)


def add_years(date_time, years):
	try:
		return date_time.replace(year=date_time.year + years)
	except ValueError:
		return date_time + (datetime(date_time.year + years, 3, 1) - datetime(date_time.year, 3, 1))


def datetime_now():
	if debug_time is None:
		return datetime_force_utc(datetime.utcnow().replace(microsecond=0))
	else:
		return debug_time


def datetime_from_timestamp(timestamp):
	return datetime_force_utc(datetime.utcfromtimestamp(timestamp))


def get_datetime_string(date_time, convert_utc=True, format_string="%Y-%m-%d %H:%M:%S"):
	if date_time is None:
		return ""
	if convert_utc:
		date_time = datetime_as_utc(date_time)
	return date_time.strftime(format_string)


def parse_datetime_string(date_time_string, force_utc=True, format_string="%Y-%m-%d %H:%M:%S"):
	if date_time_string is None or date_time_string == "None" or date_time_string == "":
		return None
	date_time = datetime.strptime(date_time_string, format_string)
	if force_utc:
		date_time = datetime_force_utc(date_time)
	return date_time


def html_encode(message):
	return urllib.parse.quote(message, safe='')


def build_message_link(recipient, subject, content=None):
	base = "https://np.reddit.com/message/compose/?"
	bldr = str_bldr()
	bldr.append(f"to={recipient}")
	bldr.append(f"subject={html_encode(subject)}")
	if content is not None:
		bldr.append(f"message={html_encode(content)}")

	return base + '&'.join(bldr)


def replace_np(link):
	return re.sub(r"(www|old|new)\.reddit\.com", "np.reddit.com", link)


def get_footer(bldr=None):
	if bldr is None:
		bldr = str_bldr()
	bldr.append("\n\n")
	bldr.append("*****")
	bldr.append("\n\n")

	bldr.append("|[^(Info)](https://np.reddit.com/r/RemindMeBot/comments/c5l9ie/remindmebot_info_v20/)")
	bldr.append("|[^(Custom)](")
	bldr.append(build_message_link(
		static.ACCOUNT_NAME,
		"Reminder",
		f"[Link or message inside square brackets]\n\n{static.TRIGGER}! Time period here"
	))
	bldr.append(")")
	bldr.append("|[^(Your Reminders)](")
	bldr.append(build_message_link(
		static.ACCOUNT_NAME,
		"List Of Reminders",
		"MyReminders!"
	))
	bldr.append(")")
	bldr.append("|[^(Feedback)](")
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


def requests_available(requests_pending):
	if requests_pending == 0:
		return 0
	elif requests_pending < 200:
		return 30
	else:
		return min(1000, int(requests_pending / 5))
