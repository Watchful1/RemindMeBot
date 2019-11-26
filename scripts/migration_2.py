import discord_logging
import re

log = discord_logging.init_logging()

import reddit_class
from database_old import DatabaseOld

reddit = reddit_class.Reddit("Watchful1BotTest", False)
database = Database()

count_no_source = 0
count_comment_id = 0
count_comment_missing = 0
count_comment_else = 0
count_reminders_updated = 0
reminders = database.get_all_reminders()
for i, reminder in enumerate(reminders):
	if i % 1000 == 0:
		log.info(f"{i}/{len(reminders)}: {count_no_source} : {count_comment_id} : {count_comment_missing} : {count_comment_else}")
	if "reddit.com" not in reminder.source:
		changed = False
		if "Unfortunately I couldn't find a source for this reminder. This happens sometimes with really " \
		   "old reminders" in reminder.source:
			count_no_source += 1
			reminder.source = "No source"
			changed = True

		else:
			match = re.search(r"^(\w{7})$", reminder.source)
			if match is not None:
				comment = reddit.get_comment(match.group())
				try:
					permalink = f"https://www.reddit.com{comment.permalink}"
					reminder.source = permalink
					count_comment_id += 1
					changed = True

				except Exception:
					count_comment_missing += 1

			else:
				count_comment_else += 1

		if changed:
			database.add_reminder(reminder)
			count_reminders_updated += 1

log.info(f"{len(reminders)}/{len(reminders)}: {count_no_source} : {count_comment_id} : {count_comment_missing} : {count_comment_else}")
log.info(f"Reminders updated: {count_reminders_updated}")
