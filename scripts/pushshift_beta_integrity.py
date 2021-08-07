import discord_logging
from datetime import timedelta
import requests
import time

log = discord_logging.init_logging()

import utils

USER_AGENT = "Pushshift tester by u/Watchful1"
LAST_REQUEST = utils.datetime_now() - timedelta(seconds=1)


def get_comments(date_time):
	global LAST_REQUEST
	seconds_since_last_request = (utils.datetime_now() - LAST_REQUEST).total_seconds()
	if seconds_since_last_request < 1:
		#log.info(f"Sleeping: {1 - seconds_since_last_request}")
		time.sleep(1 - seconds_since_last_request)

	url = f"https://beta.pushshift.io/search/reddit/comments?size=250&sort=desc&max_created_utc={int(date_time.timestamp())}"
	LAST_REQUEST = utils.datetime_now()
	for i in range(10):
		try:
			response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
			if response.status_code != 200:
				log.warning(f"Bad response code, trying again: {response.status_code} : {url}")
				time.sleep(5)
				continue
			comments = response.json()['data']
			return comments
		except Exception as err:
			log.warning(f"Exception in request, trying again: {err}")
			time.sleep(5)
			continue
	log.warning(f"Hit 10 exceptions, giving up")
	return None


end_time = utils.parse_datetime_string("2021-06-03 02:45:00")
start_time = utils.datetime_now() - timedelta(seconds=30)
log.info(f"Counting comments from {utils.get_datetime_string(start_time, False)} to {utils.get_datetime_string(end_time, False)}, {int((start_time - end_time).total_seconds())} seconds")
current_time = start_time

current_count = 0
while current_time > end_time:
	current_comments = get_comments(current_time)
	if current_comments is None:
		break
	ingest_delay_seconds = int((utils.datetime_from_timestamp(current_comments[0]['retrieved_utc']) - utils.datetime_from_timestamp(current_comments[0]['created_utc'])).total_seconds())
	for comment in current_comments:
		comment_time = utils.datetime_from_timestamp(comment['created_utc'])
		if comment_time != current_time:
			log.info(f"{utils.get_datetime_string(current_time)}	{current_count}	{ingest_delay_seconds if current_count > 0 else 0}")
			current_count = 0
			current_time = current_time - timedelta(seconds=1)
			break
		current_count += 1
