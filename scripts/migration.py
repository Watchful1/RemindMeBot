import sqlite3
import discord_logging
import time
import os

log = discord_logging.init_logging()

from classes.reminder import Reminder
import utils
from database_old import Database


old_database = "databaseOld.db"
new_database = "database_old.db"

log.info(f"Importing from {old_database} to {new_database}")

old_db_conn = sqlite3.connect(old_database)
old_c = old_db_conn.cursor()

if os.path.exists(new_database):
	log.info("Deleting existing database_old")
	os.remove(new_database)
new_db_conn = sqlite3.connect(new_database)
new_c = new_db_conn.cursor()
new_c.execute(Database.tables['reminders'])

default_comment = "Hello, I'm here to remind you to see the parent comment!"
info_page = "http://np.reddit.com/r/RemindMeBot/comments/24duzp/remindmebot_info/"

startTime = time.perf_counter()
loop = 0
count_default_comment = 0
count_info_page = 0
for row in old_c.execute('''
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
			reminder.source = "Unfortunately I couldn't find a source for this reminder. " \
				"This happens sometimes with really old reminders"

		new_c.execute('''
			INSERT INTO reminders
			(Source, RequestedDate, TargetDate, Message, User, Defaulted)
			VALUES (?, ?, ?, ?, ?, 0)
		''', (
			reminder.source,
			utils.get_datetime_string(reminder.requested_date),
			utils.get_datetime_string(reminder.target_date),
			reminder.message,
			reminder.user))
	except Exception as err:
		log.info(err)
		log.info(reminder)
	if loop % 10000 == 0:
		log.info(f"{loop}: {int(time.perf_counter() - startTime)}s : {count_default_comment} : {count_info_page}")

new_db_conn.commit()
new_db_conn.close()
old_db_conn.close()
log.info(f"{loop}: {int(time.perf_counter() - startTime)}s : {count_default_comment} : {count_info_page}")
