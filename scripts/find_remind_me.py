import discord_logging
from datetime import datetime
import static
import requests
import re

log = discord_logging.init_logging()

import utils

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remind%20me&before="


def trigger_start_of_text(body, trigger):
	return body.startswith(f"{trigger}!") or body.startswith(f"!{trigger}")


def trigger_in_text(body, trigger):
	return f"{trigger}!" in body or f"!{trigger}" in body


def find_reminder_time(body):
	regex_string = r'(?:remind me.? *)(.*?)(?:\[|\n|\"|“|$)'
	times = re.findall(regex_string, body, flags=re.IGNORECASE)
	if len(times) > 0 and times[0] != "":
		return times[0][:100]
	else:
		return None


previousEpoch = int(datetime.utcnow().timestamp())
count = 0
breakOut = False
while True:
	newUrl = url+str(previousEpoch)
	json = requests.get(newUrl, headers={'User-Agent': "Remindme tester by /u/Watchful1"})
	objects = json.json()['data']
	if len(objects) == 0:
		break
	for comment in objects:
		if comment['author'] == "RemindMeBot" or comment['subreddit'] == "RemindMeBot":
			continue
		previousEpoch = comment['created_utc'] - 1
		comment_created = utils.datetime_from_timestamp(comment['created_utc'])
		body = comment['body'].lower().strip()
		trigger_in = trigger_in_text(body, "remind me")
		trigger_start = trigger_start_of_text(body, "remind me")
		time_string = ""
		target_date = None
		if trigger_in:
			time_string = find_reminder_time(body)
			if time_string is not None:
				target_date = utils.parse_time(time_string, comment_created, None)
			else:
				time_string = ""

		if trigger_in and target_date is not None and not trigger_start:
			log.info(f"{'1' if trigger_in else ' '}|{'1' if trigger_start else ' '}|{'1' if target_date else ' '}| {time_string.ljust(100)} | https://www.reddit.com{comment['permalink']}")
		count += 1
		if count % 1000 == 0:
			log.info(f"{count} | {utils.get_datetime_string(comment_created)}")
		if count > 100000:
			breakOut = True
			break
	if breakOut:
		break
