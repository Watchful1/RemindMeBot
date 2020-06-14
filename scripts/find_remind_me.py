import discord_logging
from datetime import datetime
import static
import requests
import re

log = discord_logging.init_logging(debug=True)

import utils

trigger = "remindme"
trigger_split = "remind me"

url = f"https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=" \
	  f"{'|'.join([trigger, trigger_split.replace(' ', '%20')])}" \
	  f"&before="


def trigger_start_of_text(body, trigger):
	return body.startswith(f"{trigger}!") or body.startswith(f"!{trigger}")


def trigger_start_of_line(body, trigger):
	for line in body.splitlines():
		if line.startswith(f"{trigger}!") or line.startswith(f"!{trigger}"):
			return True
	return False


def trigger_in_text(body, trigger):
	return f"{trigger}!" in body or f"!{trigger}" in body


def parse_comment(body, trigger, comment_created):
	time_string = utils.find_reminder_time(body, trigger)
	time_string = time_string.strip() if time_string is not None else None
	target_date = None
	if time_string is not None:
		target_date = utils.parse_time(time_string, comment_created, None)
	return time_string, target_date



previousEpoch = int(datetime.utcnow().timestamp())
count = 0
breakOut = False
trigger_count = 0
trigger_split_start_count = 0
trigger_split_start_string_count = 0
trigger_split_start_date_count = 0
trigger_split_count = 0
trigger_split_string_count = 0
trigger_split_date_count = 0
count_none = 0
while True:
	newUrl = url+str(previousEpoch)
	json = requests.get(newUrl, headers={'User-Agent': "Remindme tester by /u/Watchful1"})
	objects = json.json()['data']
	if len(objects) == 0:
		break
	for comment in objects:
		previousEpoch = comment['created_utc'] - 1
		if comment['author'] not in static.BLACKLISTED_ACCOUNTS and comment['subreddit'] != "RemindMeBot":
			body = comment['body'].lower().strip()
			trigger = None
			if trigger_in_text(body, trigger):
				#log.debug(f"Trigger: https://reddit.com{comment['permalink']}")
				trigger_count += 1
			elif trigger_start_of_line(body, trigger_split):
				time_string, target_date = parse_comment(comment['body'], trigger_split, utils.datetime_from_timestamp(comment['created_utc']))
				trigger_split_start_count += 1
				if time_string is not None:
					trigger_split_start_string_count += 1
				if target_date is not None:
					trigger_split_start_date_count += 1
				if time_string is None:
					log.debug(f"Start no string: https://reddit.com{comment['permalink']}")
				elif target_date is None:
					log.debug(f"Start no date  : https://reddit.com{comment['permalink']}")
			elif trigger_in_text(body, trigger_split):
				time_string, target_date = parse_comment(comment['body'], trigger_split, utils.datetime_from_timestamp(comment['created_utc']))
				trigger_split_count += 1
				if time_string is not None:
					trigger_split_string_count += 1
				if target_date is not None:
					trigger_split_date_count += 1
				# if time_string is None:
				# 	log.debug(f"Split no string: https://reddit.com{comment['permalink']}")
				# elif target_date is None:
				# 	log.debug(f"Split no date  : https://reddit.com{comment['permalink']}")
			else:
				count_none += 1

		count += 1
		if count % 1000 == 0:
			log.info(f"{count} | {utils.get_datetime_string(utils.datetime_from_timestamp(comment['created_utc']))}")
		if count >= 5000:
			breakOut = True
			break
	if breakOut:
		break

log.info(f"trigger {trigger_count}")
log.info(f"trigger split {trigger_split_count} : string {trigger_split_string_count} : date {trigger_split_date_count}")
log.info(f"trigger split start {trigger_split_start_count} : string {trigger_split_start_string_count} : date {trigger_split_start_date_count}")
