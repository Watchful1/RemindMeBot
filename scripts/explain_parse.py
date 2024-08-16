import discord_logging
import parsedatetime
import pytz
import dateparser
import re
import sys
from dateparser.search import search_dates

log = discord_logging.init_logging()

import utils

cal = parsedatetime.Calendar()

input_string = '''!remindme 30th of February, 2024.'''
base_time_string = "2023-04-27 02:45:19 -0700"
timezone_string = None  # "America/New_York"

if base_time_string:
	base_time = utils.datetime_as_timezone(utils.parse_datetime_string(base_time_string, False, '%Y-%m-%d %H:%M:%S %z'), "UTC")
else:
	base_time = utils.datetime_now()

format_string = '%Y-%m-%d %H:%M:%S %Z'

log.info(f"Input string: {input_string}")
time = utils.find_reminder_time(input_string, "remindme")
if time is not None:
	log.info(f"Result: {time}")
	time_string = time
else:
	log.info(f"No string found")
	sys.exit(0)

log.info(f"Now: {base_time.strftime(format_string)}")
#
# try:
date_time = dateparser.parse(time_string, languages=['en'], settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
if date_time is not None:
	log.info(f"dateparser.parse: {date_time.strftime(format_string)}")
# except Exception:
# 	date_time = None

try:
	results = search_dates(time_string, languages=['en'], settings={"PREFER_DATES_FROM": 'future', "RELATIVE_BASE": base_time.replace(tzinfo=None)})
	if results is not None:
		temp_time = results[0][1]
		if temp_time.tzinfo is None:
			temp_time = utils.datetime_force_utc(temp_time)

		if temp_time > base_time:
			if date_time is None:
				date_time = results[0][1]
				log.info(f"search_dates: {date_time.strftime(format_string)}")
			else:
				log.info(f"    search_dates would have found: {results[0][1].strftime(format_string)}")
except Exception:
	date_time = None

try:
	date_time_result, result_code = cal.parseDT(time_string, base_time)
	if result_code != 0:
		if date_time is None:
			date_time = date_time_result
			log.info(f"cal.parseDT: {date_time.strftime(format_string)}")
		else:
			log.info(f"    cal.parseDT would have found: {date_time_result.strftime(format_string)}")
except Exception:
	date_time = None


if date_time is None:
	log.info(f"No datetime found")
	sys.exit(0)

if date_time.tzinfo is None:
	if timezone_string is not None:
		date_time = pytz.timezone(timezone_string).localize(date_time)
		log.info(f"Converting to timezone: {timezone_string} : {date_time.strftime(format_string)}")
	else:
		date_time = utils.datetime_force_utc(date_time)
		log.info(f"Converting to utc: {date_time.strftime(format_string)}")

date_time = utils.datetime_as_utc(date_time)
log.info(f"Forcing utc: {date_time.strftime(format_string)}")
