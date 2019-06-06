import sqlite3
import discord_logging
import time

log = discord_logging.init_logging()

from classes.reminder import Reminder
import utils


dbConn = sqlite3.connect("databaseLive.db")
c = dbConn.cursor()

default_comment = "Hello, I'm here to remind you to see the parent comment!"
info_page = "http://np.reddit.com/r/RemindMeBot/comments/24duzp/remindmebot_info/"

startTime = time.perf_counter()
loop = 0
count_default_comment = 0
count_info_page = 0
count_info_both = 0
for row in c.execute('''
	SELECT permalink, message, new_date, origin_date, userID
	FROM message_date
	'''):
	loop += 1
	reminder = Reminder(
		source=row[0],
		target_date=utils.parse_datetime_string(row[2]),
		message=row[1],
		user=row[4],
		requested_date=utils.parse_datetime_string(row[3])
	)
	try:
		if isinstance(reminder.message, (bytes, bytearray)):
			reminder.message = reminder.message.decode("utf-8")
		reminder.message = reminder.message.strip(' "')
		if reminder.message == default_comment:
			count_default_comment += 1
			reminder.message = None

		if isinstance(reminder.source, (bytes, bytearray)):
			reminder.source = reminder.source.decode("utf-8")
		if reminder.source == info_page:
			count_info_page += 1

		if reminder.message is None and reminder.source == info_page:
			count_info_both += 1
	except Exception as err:
		log.info(err)
		log.info(reminder)
	if loop % 10000 == 0:
		log.info(f"{loop}: {int(time.perf_counter() - startTime)}s : {count_default_comment} : {count_info_page} : {count_info_both}")

log.info(f"{loop}: {int(time.perf_counter() - startTime)}s : {count_default_comment} : {count_info_page} : {count_info_both}")
