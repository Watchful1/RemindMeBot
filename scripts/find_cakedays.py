import discord_logging
from datetime import datetime
import static
import requests

log = discord_logging.init_logging()

import utils

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&q=cakeday&before="


def trigger_start_of_text(body, trigger):
	return body.startswith(f"{trigger}!") or body.startswith(f"!{trigger}")


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
		if comment['author'] == "RemindMeBot":
			continue
		if comment['subreddit'] == "RemindMeBot":
			continue
		previousEpoch = comment['created_utc'] - 1
		if trigger_start_of_text(comment['body'].lower(), "cakeday"):
			log.info(f"https://www.reddit.com{comment['permalink']}")
		count += 1
		if count % 1000 == 0:
			log.info(f"{count} | {utils.get_datetime_string(utils.datetime_from_timestamp(comment['created_utc']))}")
		if count > 100000:
			breakOut = True
			break
	if breakOut:
		break
