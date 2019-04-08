import sqlite3
import logging
import os
from datetime import datetime
from shutil import copyfile

from classes.reminder import Reminder
import static
import utils

log = logging.getLogger("bot")


class Database:
	def __init__(self, debug, clone=False):
		if debug:
			if clone:
				if os.path.exists(static.DATABASE_DEBUG_NAME):
					os.remove(static.DATABASE_DEBUG_NAME)
				copyfile(static.DATABASE_NAME, static.DATABASE_DEBUG_NAME)

			self.dbConn = sqlite3.connect(static.DATABASE_DEBUG_NAME)
		else:
			self.dbConn = sqlite3.connect(static.DATABASE_NAME)

		c = self.dbConn.cursor()
		if debug and not clone:
			c.execute('''
				DROP TABLE IF EXISTS reminders
			''')
			c.execute('''
				DROP TABLE IF EXISTS comments
			''')

		c.execute('''
			CREATE TABLE IF NOT EXISTS reminders (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				Source VARCHAR(400) NOT NULL,
				RequestedDate TIMESTAMP NOT NULL,
				TargetDate TIMESTAMP NOT NULL,
				Message VARCHAR(500) NOT NULL,
				User VARCHAR(80) NOT NULL
			)
		''')
		c.execute('''
			CREATE TABLE IF NOT EXISTS comments (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				ThreadID VARCHAR(12) NOT NULL,
				CommentID VARCHAR(12) NOT NULL,
				CurrentCount INTEGER DEFAULT 1,
				SourceID VARCHAR(12) NOT NULL,
				TargetDate TIMESTAMP NOT NULL,
				UNIQUE (ThreadID)
			)
		''')
		self.dbConn.commit()

	def close(self):
		self.dbConn.commit()
		self.dbConn.close()

	def save_reminder(self, reminder):
		if not isinstance(reminder, Reminder):
			return False
		if reminder.db_id is not None:
			return False

		c = self.dbConn.cursor()
		try:
			c.execute('''
				INSERT INTO reminders
				(Source, RequestedDate, TargetDate, Message, User)
				VALUES (?, ?, ?, ?, ?)
			''', (reminder.source,
				utils.datetime_as_utc(reminder.requested_date).strftime("%Y-%m-%d %H:%M:%S"),
				utils.datetime_as_utc(reminder.target_date).strftime("%Y-%m-%d %H:%M:%S"),
				reminder.message,
				reminder.user))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save reminder: {err}")
			return False

		if c.lastrowid is not None:
			reminder.db_id = c.lastrowid

		self.dbConn.commit()

		return True

	def get_pending_reminders(self):
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User
			FROM reminders
			WHERE TargetDate < CURRENT_TIMESTAMP
			'''):
			reminder = Reminder(
				source=row[1],
				target_date=utils.datetime_force_utc(datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.datetime_force_utc(datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
			)
			results.append(reminder)

		return results

	def get_user_reminders(self, username):
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User
			FROM reminders
			WHERE User = ?
			''', (username,)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.datetime_force_utc(datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.datetime_force_utc(datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
			)
			results.append(reminder)

		return results

	def get_reminder(self, reminder_id):
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User
			FROM reminders
			WHERE ID = ?
			''', (reminder_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			return None

		reminder = Reminder(
			source=result[1],
			target_date=utils.datetime_force_utc(datetime.strptime(result[3], "%Y-%m-%d %H:%M:%S")),
			message=result[4],
			user=result[5],
			db_id=result[0],
			requested_date=utils.datetime_force_utc(datetime.strptime(result[2], "%Y-%m-%d %H:%M:%S"))
		)

		return reminder

	def delete_reminder(self, reminder):
		if reminder.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM reminders
			WHERE ID = ?
		''', (reminder.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			return True
		else:
			return False

	def delete_user_reminders(self, user):
		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM reminders
			WHERE User = ?
		''', (user,))
		self.dbConn.commit()

		return c.rowcount
