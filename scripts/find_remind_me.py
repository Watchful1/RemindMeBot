import discord_logging
from datetime import datetime, timedelta
import static
import requests
import re

log = discord_logging.init_logging(debug=True)

import utils

trigger_single = "remindme"
trigger_split = "remind me"
endEpoch = int((datetime.utcnow() - timedelta(days=3)).timestamp())

# url = f"https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=" \
# 	  f"{'|'.join([trigger, trigger_split.replace(' ', '%20')])}" \
# 	  f"&before="

base_url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q={}&before="


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


def process_comment(comment, trigger, is_start):
	body = comment['body'].lower().strip()

	trigger_found = False
	string_found = False
	date_found = False
	if is_start:
		if trigger_start_of_line(body, trigger):
			trigger_found = True

	elif trigger_in_text(body, trigger):
		trigger_found = True

	if trigger_found:
		time_string, target_date = parse_comment(comment['body'], trigger, utils.datetime_from_timestamp(comment['created_utc']))
		if time_string is not None:
			string_found = True
		if target_date is not None:
			date_found = True

	return trigger_found, string_found, date_found


def process_comments(trigger, is_start):
	previousEpoch = int(datetime.utcnow().timestamp())
	breakOut = False
	url = base_url.format(trigger)
	count = 0
	trigger_count = 0
	trigger_string_count = 0
	trigger_date_count = 0
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
				trigger_found, string_found, date_found = process_comment(comment, trigger, is_start)
				if trigger_found:
					trigger_count += 1
				if string_found:
					trigger_string_count += 1
				if date_found:
					trigger_date_count += 1
				if not trigger_found and not string_found and not date_found:
					count_none += 1

			count += 1
			if count % 1000 == 0:
				log.info(f"{count} | {utils.get_datetime_string(utils.datetime_from_timestamp(comment['created_utc']))}")
			if previousEpoch < endEpoch:
				breakOut = True
				break
		if breakOut:
			break

	log.info(f"{trigger} {trigger_count} : string {trigger_string_count} : date {trigger_date_count}")


process_comments(trigger_single, False)
process_comments(trigger_split, True)
