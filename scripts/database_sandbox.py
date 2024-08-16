import discord_logging
import sqlalchemy
from datetime import datetime, timedelta
import os

log = discord_logging.init_logging()

from database import Database
from classes.comment import DbComment
from classes.reminder import Reminder
from classes.subreddit import Subreddit
from classes.user import User
import utils

if __name__ == "__main__":
	backup_folder = r"D:\backup\RemindMeBot"
	date_str = "24-05-15 00:00"
	backup_before = datetime.strptime(date_str, "%y-%m-%d %H:%M")

	found = False
	for subdir, dirs, files in os.walk(backup_folder):
		for filename in reversed(files):
			if filename.endswith(".db"):
				input_path = os.path.join(subdir, filename)
				try:
					backup_date = datetime.strptime(filename[:-3], "%Y-%m-%d_%H-%M")
					if backup_date > backup_before:
						continue

					database = Database(override_location=input_path, readonly=True, quiet=True)
					user = database.get_or_add_user("SilynJaguar")
					reminders = database.session.query(Reminder).filter_by(user=user).all()
					#log.info(f"{backup_date}: {banned_count}")
					database.close()
					found = True
					break
				except (ValueError, sqlalchemy.exc.OperationalError):
					continue
		if found:
			break
