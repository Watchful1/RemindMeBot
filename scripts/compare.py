import discord_logging
import parsedatetime.parsedatetime as pdt
from datetime import datetime
from datetime import timedelta
import time
import requests
import re

log = discord_logging.init_logging()

import utils

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remindme&before="

previousEpoch = int(datetime.utcnow().timestamp())
count = 0
breakOut = False
current = utils.datetime_now()
current_hour = current.replace(year=1, month=1, day=1)
zero_hour = current.replace(year=1, month=1, day=1, hour=0, minute=0, second=0)
while True:
	newUrl = url+str(previousEpoch)
	json = requests.get(newUrl, headers={'User-Agent': "Remindme tester by /u/Watchful1"})
	objects = json.json()['data']
	if len(objects) == 0:
		break
	for comment in objects:
		previousEpoch = comment['created_utc'] - 1
		regex_string = r'(?:remindme.? )(.*?)(?:\[|\n|\"|$)'
		times = re.findall(regex_string, comment['body'], flags=re.IGNORECASE)
		if len(times) > 0:
			time_string = times[0]

			try:
				cal = pdt.Calendar()
				holdTime = cal.parse(time_string, current)
				old_date = time.strftime('%Y-%m-%d %H:%M:%S', holdTime[0])
			except Exception:
				old_date = "None"

			try:
				new_date = utils.get_datetime_string(utils.parse_time(time_string, current), format_string='%Y-%m-%d %H:%M:%S')
			except Exception:
				new_date = "None"

			if old_date != new_date and old_date != utils.get_datetime_string(current, format_string='%Y-%m-%d %H:%M:%S'):
				old_date_time = utils.parse_datetime_string(old_date)
				new_date_time = utils.parse_datetime_string(new_date)
				if old_date_time is None or new_date_time is None or \
						not (old_date_time.replace(year=1, month=1, day=1) == current_hour and
						new_date_time.replace(year=1, month=1, day=1) == zero_hour):
					log.info(f"{old_date.ljust(19)} | {new_date.ljust(19)} | {time_string}")
#{utils.reddit_link(comment['permalink']).ljust(120)} |
		count += 1
		# if count % 1000 == 0:
		# 	log.info("comments: {}, {}".format(count, datetime.fromtimestamp(previousEpoch).strftime("%Y-%m-%d")))
		if count > 2000:
			breakOut = True
			break
	if breakOut:
		break



# current = utils.datetime_now()
# times = [
#     "One Year",
#     "3 Months",
#     "One Week",
#     "1 Day",
#     "33 Hours",
#     "10 Minutes",
#     "August 25th, 2014",
#     "25 Aug 2014",
#     "5pm August 25",
#     "Next Saturday",
#     "Tomorrow",
#     "Next Thursday at 4pm",
#     "Tonight",
#     "at 4pm",
#     "2 Hours After Noon",
#     "eoy",
#     "eom",
#     "eod",
# ]
#
# log.info(f"Base time: {current.strftime('%Y-%m-%d %H:%M:%S %Z')}")
# for time_string in times:
# 	try:
# 		cal = pdt.Calendar()
# 		holdTime = cal.parse(time_string, current)
# 		old_date = time.strftime('%Y-%m-%d %H:%M:%S', holdTime[0])
# 	except Exception:
# 		old_date = "failed"
#
# 	try:
# 		new_date = utils.get_datetime_string(utils.parse_time(time_string, current), format_string='%Y-%m-%d %H:%M:%S %Z')
# 	except Exception:
# 		new_date = "failed"
#
# 	log.info(f"{time_string.ljust(20)} | {old_date.ljust(19)} | {new_date.ljust(19)}")
