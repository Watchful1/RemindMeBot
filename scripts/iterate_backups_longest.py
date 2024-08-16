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

	for subdir, dirs, files in os.walk(backup_folder):
		for filename in files:
			if filename.endswith(".db"):
				input_path = os.path.join(subdir, filename)
				try:
					backup_date = datetime.strptime(filename[:-3], "%Y-%m-%d_%H-%M")

					database = Database(override_location=input_path, readonly=True, quiet=True)
					banned_count = database.session.query(Subreddit).filter_by(banned=True).count()
					log.info(f"{backup_date}: {banned_count}")
					database.close()
				except (ValueError, sqlalchemy.exc.OperationalError):
					continue
