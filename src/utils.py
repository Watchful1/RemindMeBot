import re
import discord_logging
import dateparser
from dateutil.relativedelta import relativedelta
from dateparser.search import search_dates
import parsedatetime
import pytz
from datetime import datetime
from datetime import timedelta
import urllib.parse
import prawcore

import counters
import static

log = discord_logging.get_logger()
debug_time = None
cal = parsedatetime.Calendar()


def process_error(message, exception, traceback):
	is_transient = isinstance(exception, prawcore.exceptions.ServerError)
	log.warning(f"{message}: {exception}")
	if is_transient:
		log.info(traceback)
		counters.errors.labels(type='api').inc()
	else:
		log.warning(traceback)
		counters.errors.labels(type='other').inc()

	return is_transient


def find_reminder_message(body, trigger):
	line_match = re.search(
		r'(?:{trigger}.+)(?:(?:\[)([^\]]+?)(?:\])|(?:\")([^\"]+?)(?:\")|(?:“)([^”]*?)(?:”))(?:[^(]|\n|$)'.format(
			trigger=trigger),
		body,
		flags=re.IGNORECASE)
	if line_match:
		return line_match.group(1) or line_match.group(2) or line_match.group(3)

	match = re.search(
		r'(?:(?:\[)([^\]]+?)(?:\])|(?:\")([^\"]+?)(?:\")|(?:“)([^”]*?)(?:”))(?:[^(]|\n|$)',
		body,
		flags=re.IGNORECASE)
	if match:
		return match.group(1) or match.group(2) or match.group(3)
	else:
		return None


def find_reminder_time(body, trigger):
	regex_string = r'(?:{trigger}.? +)(.*?)(?:\[|\n|\"|“|$)'.format(trigger=trigger)
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0][:80]

	regex_string = r'(?:{trigger}.? *)(.*?)(?:\[|\n|\"|“|$)'.format(trigger=trigger)
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0][:80]
	else:
		return None


def parse_time(time_string, base_time, timezone_string):
	base_time = datetime_as_timezone(base_time, timezone_string)

	try:
		date_time = dateparser.parse(
			time_string,
			settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
	except Exception:
		date_time = None

	if date_time is None:
		try:
			results = search_dates(
				time_string,
				languages=['en'],
				settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
			if results is not None:
				temp_time = results[0][1]
				if temp_time.tzinfo is None:
					temp_time = datetime_force_utc(temp_time)

				if temp_time > base_time:
					date_time = results[0][1]
			else:
				date_time = None
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

	date_time = datetime_as_utc(date_time)

	return date_time


def render_time(date_time, user=None, format_string=None):
	timezone = user.timezone if user is not None else None
	time_format = user.time_format if user is not None else None
	if format_string is None:
		if time_format == "12":
			format_string = "%Y-%m-%d %I:%M:%S %p %Z"
		else:
			format_string = "%Y-%m-%d %H:%M:%S %Z"

	bldr = str_bldr()
	bldr.append("[**")
	bldr.append(datetime_as_timezone(date_time, timezone).strftime(format_string))
	bldr.append("**](http://www.wolframalpha.com/input/?i=")
	bldr.append(date_time.strftime('%Y-%m-%d %H:%M:%S %Z').replace(" ", "%20"))
	bldr.append(" To Local Time".replace(" ", "%20"))
	bldr.append(")")
	return ''.join(bldr)


def render_time_diff(start_date, end_date):
	seconds = int((end_date - start_date).total_seconds())
	if seconds > 59:
		delta = relativedelta(
			start_date + relativedelta(seconds=min(seconds * 1.02, seconds + 60 * 60 * 24)),
			start_date)
	else:
		delta = relativedelta(end_date, start_date)
	if delta.years > 0:
		return f"{delta.years} year{('s' if delta.years > 1 else '')}"
	elif delta.months > 0:
		return f"{delta.months} month{('s' if delta.months > 1 else '')}"
	elif delta.days > 0:
		return f"{delta.days} day{('s' if delta.days > 1 else '')}"
	elif delta.hours > 0:
		return f"{delta.hours} hour{('s' if delta.hours > 1 else '')}"
	elif delta.minutes > 0:
		return f"{delta.minutes} minute{('s' if delta.minutes > 1 else '')}"
	elif delta.seconds > 0:
		return f"{delta.seconds} second{('s' if delta.seconds > 1 else '')}"
	else:
		return ""


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


def get_next_anniversary(account_created_utc):
	if account_created_utc is None:
		log.info("Account creation date is none")
		return datetime_now()
	account_created = datetime_from_timestamp(account_created_utc)
	next_anniversary = add_years(account_created, datetime_now().year - account_created.year)
	if next_anniversary < datetime_now():
		next_anniversary = add_years(next_anniversary, 1)

	log.debug(
		f"Account created {get_datetime_string(account_created)}, anniversary {get_datetime_string(next_anniversary)}")
	return next_anniversary


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

	bldr.append("|[^(Info)](")
	bldr.append(replace_np(static.INFO_POST))
	bldr.append(")|[^(Custom)](")
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
		"RemindMeBot Feedback"
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


def check_append_context_to_link(link):
	if re.search(r"reddit\.com/r/\w+/comments/(\w+/){3}", link):
		return link + "?context=3"
	else:
		return link
