import discord_logging
from datetime import datetime, timedelta
import static
import requests
import re

log = discord_logging.init_logging(debug=True)

import utils

trigger_single = "remindme"
trigger_split = "remind me"
endEpoch = int((datetime.utcnow() - timedelta(days=1)).timestamp())

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


def process_comment(comment):
	body = comment['body'].lower().strip()

	single_trigger_found = False
	single_string_found = False
	single_date_found = False
	if trigger_in_text(body, trigger_single):
		single_trigger_found = True

	if single_trigger_found:
		time_string, target_date = parse_comment(comment['body'], trigger_single, utils.datetime_from_timestamp(comment['created_utc']))
		if time_string is not None:
			single_string_found = True
		if target_date is not None:
			single_date_found = True

	split_trigger_found = False
	split_string_found = False
	split_date_found = False
	if trigger_start_of_line(body, trigger_split):
		split_trigger_found = True

	if split_trigger_found:
		time_string, target_date = parse_comment(comment['body'], trigger_split, utils.datetime_from_timestamp(comment['created_utc']))
		if time_string is not None:
			split_string_found = True
		if target_date is not None:
			split_date_found = True

	return single_trigger_found, single_string_found, single_date_found, split_trigger_found, split_string_found, split_date_found


def process_comments(url):
	previousEpoch = int(datetime.utcnow().timestamp())
	breakOut = False
	count = 0
	single_trigger_count = 0
	single_trigger_string_count = 0
	single_trigger_date_count = 0
	split_trigger_count = 0
	split_trigger_string_count = 0
	split_trigger_date_count = 0
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
				single_trigger_found, single_string_found, single_date_found, split_trigger_found, split_string_found, split_date_found = process_comment(comment)
				if single_trigger_found:
					single_trigger_count += 1
				if single_string_found:
					single_trigger_string_count += 1
				if single_date_found:
					single_trigger_date_count += 1
				if split_trigger_found:
					split_trigger_count += 1
				if split_string_found:
					split_trigger_string_count += 1
				if split_date_found:
					split_trigger_date_count += 1
				if not single_trigger_found and not single_string_found and not single_date_found:
					count_none += 1

			count += 1
			# if count % 1000 == 0:
			# 	log.info(f"{count} | {utils.get_datetime_string(utils.datetime_from_timestamp(comment['created_utc']))}")
			if previousEpoch < endEpoch:
				breakOut = True
				break
		if breakOut:
			break

	log.info(f"{single_trigger_count}|{single_trigger_string_count}|{single_trigger_date_count} - {split_trigger_count}|{split_trigger_string_count}|{split_trigger_date_count}")


process_comments("https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remindme&before=")
process_comments("https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remind%20me&before=")
process_comments("https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=remindme|cakeday|remindmerepeat|%22remind%20me%22&before=")

