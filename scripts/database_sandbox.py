import discord_logging
import sqlalchemy
from datetime import datetime, timedelta
import os
import json

log = discord_logging.init_logging()

from database import Database
from classes.comment import DbComment
from classes.reminder import Reminder
from classes.subreddit import Subreddit
from classes.user import User
import utils

if __name__ == "__main__":
	backup_folder = r"D:\backup\RemindMeBot"

	input_path = os.path.join(backup_folder, "2025-07-30_14-30.db")
	database = Database(override_location=input_path, readonly=True, quiet=True)

	reminders = database.get_pending_reminders(1000000000, datetime.strptime("26-12-31_23:59", "%y-%m-%d_%H:%M"))
	log.info(f"{len(reminders)} reminders found")

	users = set()
	for reminder in reminders:
		users.add(reminder.user.name)
	log.info(f"{len(users)} users found")
	users_list = []
	for user in users:
		users_list.append({"name": user, "count": 1, "sent": False, "failed": False})

	file_handle = open("remindmebot.txt", "w", encoding="utf-8")
	file_handle.write(json.dumps(users_list, indent=4))
	file_handle.close()

	# date_str = "25-07-30 02-30"
	# backup_before = datetime.strptime(date_str, "%y-%m-%d %H:%M")
	# found = False
	# for subdir, dirs, files in os.walk(backup_folder):
	# 	for filename in reversed(files):
	# 		if filename.endswith(".db"):
	# 			input_path = os.path.join(subdir, filename)
	# 			try:
	# 				backup_date = datetime.strptime(filename[:-3], "%Y-%m-%d_%H-%M")
	# 				if backup_date > backup_before:
	# 					continue
	#
	# 				database = Database(override_location=input_path, readonly=True, quiet=True)
	# 				user = database.get_or_add_user("SilynJaguar")
	# 				reminders = database.session.query(Reminder).filter_by(user=user).all()
	# 				#log.info(f"{backup_date}: {banned_count}")
	# 				database.close()
	# 				found = True
	# 				break
	# 			except (ValueError, sqlalchemy.exc.OperationalError):
	# 				continue
	# 	if found:
	# 		break
