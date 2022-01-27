import discord_logging
import re
from collections import defaultdict
from datetime import timedelta

log = discord_logging.init_logging()

from database import Database
from classes.comment import DbComment
from classes.reminder import Reminder
from classes.subreddit import Subreddit
from classes.user import User
import utils

if __name__ == "__main__":
	database = Database()

	date_after = utils.datetime_now() - timedelta(days=180)
	reminders = database.session.query(Reminder) \
		.filter(Reminder.requested_date > date_after)\
		.all()

	sub_counts = defaultdict(int)
	count_reminders = 0
	count_from_comment = 0
	for reminder in reminders:
		count_reminders += 1
		groups = re.search(r"(?:reddit.com/r/)([\w-]+)", reminder.source)
		if groups:
			count_from_comment += 1
			sub_counts[groups[1]] += 1

	print(f"Reminders: {count_reminders}, from comment: {count_from_comment}")

	database.close()

	for subreddit, count_reminder in sorted(sub_counts.items(), key=lambda item: item[1] * -1):
		if count_reminder > 1:
			log.info(f"{subreddit}	{count_reminder}")
