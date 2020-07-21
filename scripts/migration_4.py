import discord_logging

log = discord_logging.init_logging()

from database import Database
from classes.reminder import Reminder

database = Database()

comments = {
	"dp9zjr0": "/r/The_Donald/comments/7af5i7/life_comes_at_you_fast/dp9zjr0/",
	"dpavxen": "/r/The_Donald/comments/7ajz8d/this_has_not_aged_well/dpavxen/",
	"dpgq2cc": "/r/The_Donald/comments/7bb4se/persistance/dpgq2cc/",
	"dpmi1ia": "/r/CringeAnarchy/comments/7c0t7w/seen_on_some_artists_instagram_story/dpmi1ia/",
	"dpoxm7j": "/r/The_Donald/comments/7cb255/immigration_without_assimilation_is_invasion/dpoxm7j/",
	"dpqdmkm": "/r/milliondollarextreme/comments/7chna0/1968/dpqdmkm/",
	"dpqeg1a": "/r/milliondollarextreme/comments/7chna0/1968/dpqeg1a/",
	"dpuimx7": "/r/The_Donald/comments/7d1q7t/sr_16_sr_20_jr_24_jr_28_eric_32_eric_36_ivanka_40/dpuimx7/",
}

www_reminders = 0
empty_reminders = 0
starting_space_reminders = 0
comment_id_reminders = 0
test_reminders = 0
for reminder in database.session.query(Reminder).all():
	if not reminder.source.startswith("http") and reminder.source != "No source":
		if reminder.source.startswith("www"):
			reminder.source = "https://"+reminder.source
			www_reminders += 1
		else:
			if reminder.source == "":
				reminder.source = "No source"
				empty_reminders += 1
			elif reminder.source.startswith(" http"):
				reminder.source = reminder.source[1:]
				starting_space_reminders += 1
			elif reminder.source in comments:
				reminder.source = f"https://www.reddit.com{comments[reminder.source]}"
				comment_id_reminders += 1
			elif reminder.source == "TEST" or len(reminder.source) > 160:
				database.session.delete(reminder)
				test_reminders += 1
			else:
				log.info(reminder.source)

database.close()
log.info(f"www: {www_reminders}")
log.info(f"empty: {empty_reminders}")
log.info(f"space: {starting_space_reminders}")
log.info(f"comment id: {comment_id_reminders}")
log.info(f"test: {test_reminders}")
