import discord_logging
import parsedatetime
from datetime import datetime
from datetime import timedelta
import static
import re
import requests
import pytz
import dateparser
from dateparser.search import search_dates

log = discord_logging.init_logging()

import utils

cal = parsedatetime.Calendar()


def parse_time_old(time_string, base_time, timezone_string):
	time_string = re.split("http", time_string, 2, flags=re.IGNORECASE)[0]
	base_time = utils.datetime_as_timezone(base_time, timezone_string)

	try:
		date_time = dateparser.parse(
			time_string,
			languages=['en'],
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
					temp_time = utils.datetime_force_utc(temp_time)

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
			date_time = utils.datetime_force_utc(date_time)

	date_time = utils.datetime_as_utc(date_time)

	return date_time


def find_reminder_time_old(body, trigger):
	regex_string = r'(?:{trigger}.? +)(.*?)(?:\[|\n|\"|“|$|http)'.format(trigger=trigger)
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0][:80]

	regex_string = r'(?:{trigger}.? *)(.*?)(?:\[|\n|\"|“|$|http)'.format(trigger=trigger)
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0][:80]
	else:
		return None


url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remindme&before="

previousEpoch = int(datetime.utcnow().timestamp())
count = 0
breakOut = False
current = utils.datetime_now()
log.info(f"Current time: {utils.get_datetime_string(current)}")
while True:
	newUrl = url+str(previousEpoch)
	json = requests.get(newUrl, headers={'User-Agent': "Remindme tester by /u/Watchful1"})
	objects = json.json()['data']
	if len(objects) == 0:
		break
	for comment in objects:
		if comment['author'] == "RemindMeBot":
			continue
		previousEpoch = comment['created_utc'] - 1
		time_string_old = find_reminder_time_old(comment['body'].lower(), static.TRIGGER_LOWER)#find_reminder_time_old(comment['body'].lower(), False)
		time_string_new = utils.find_reminder_time(comment['body'].lower(), static.TRIGGER_LOWER)
		if time_string_old is not None:
			date_time_old = parse_time_old(time_string_old, current, None)
			date_time_new = utils.parse_time(time_string_new, current, None)

			if date_time_old != date_time_new:
				log.info(
					f"{utils.get_datetime_string(date_time_old, False, '%Y-%m-%d %H:%M:%S %Z').ljust(23) if date_time_old is not None else 'None'.ljust(23)} "
					f"| {utils.get_datetime_string(date_time_new, False, '%Y-%m-%d %H:%M:%S %Z').ljust(23) if date_time_new is not None else 'None'.ljust(23)} "
					f"| {time_string_old[:60].ljust(60) if time_string_old is not None else 'None'.ljust(60)} "
					f"| {time_string_new.ljust(60) if time_string_new is not None else 'None'.ljust(60)} "
					f"| https://www.reddit.com{comment['permalink']} ")
		count += 1
		if count > 10000:
			breakOut = True
			break
	if breakOut:
		break
