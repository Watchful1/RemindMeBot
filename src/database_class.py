import sqlite3
import logging
from datetime import datetime

from classes.reminder import Reminder
import globals
import utils

log = logging.getLogger("bot")


class Database:
	def __init__(self, debug):
		if debug:
			self.dbConn = sqlite3.connect(globals.DATABASE_DEBUG_NAME)
		else:
			self.dbConn = sqlite3.connect(globals.DATABASE_NAME)

		c = self.dbConn.cursor()
		if debug:
			c.execute('''
				DROP TABLE IF EXISTS reminders
			''')
			c.execute('''
				DROP TABLE IF EXISTS comments
			''')
		c.execute('''
			CREATE TABLE IF NOT EXISTS reminders (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				SourceID VARCHAR(12) NOT NULL,
				RequestedDate TIMESTAMP NOT NULL,
				TargetDate TIMESTAMP NOT NULL,
				Message VARCHAR(11000) NOT NULL,
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
				(SourceID, RequestedDate, TargetDate, Message, User)
				VALUES (?, ?, ?, ?, ?)
			''', (reminder.source_id,
				  utils.datetime_as_utc(reminder.requested_date).strftime("%Y-%m-%d %H:%M:%S"),
				  utils.datetime_as_utc(reminder.target_date).strftime("%Y-%m-%d %H:%M:%S"),
				  reminder.message,
				  reminder.user))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save reminder: {err}")
			return False

		self.dbConn.commit()

		return True

	def get_reminders(self):
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, SourceID, RequestedDate, TargetDate, Message, User
			FROM reminders
			WHERE TargetDate < CURRENT_TIMESTAMP
			'''):
			reminder = Reminder(
				source_id=row[1],
				target_date=utils.datetime_force_utc(datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.datetime_force_utc(datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"))
			)
			results.append(reminder)

		return results

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
