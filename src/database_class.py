import sqlite3
import logging
import os
from datetime import datetime
from shutil import copyfile

from classes.reminder import Reminder
from classes.comment import DbComment
import static
import utils

log = logging.getLogger("bot")


class Database:
	tables = {
		'reminders': '''
			CREATE TABLE IF NOT EXISTS reminders (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				Source VARCHAR(400) NOT NULL,
				RequestedDate TIMESTAMP NOT NULL,
				TargetDate TIMESTAMP NOT NULL,
				Message VARCHAR(500) NULL,
				User VARCHAR(80) NOT NULL,
				CommentID VARCHAR(12) NULL
			)
		''',
		'comments': '''
			CREATE TABLE IF NOT EXISTS comments (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				ThreadID VARCHAR(12) NOT NULL,
				ReminderId INTEGER NOT NULL,
				CurrentCount INTEGER DEFAULT 1,
				Source VARCHAR(400) NOT NULL,
				UNIQUE (ThreadID)
			)
		''',
		'keystore': '''
			CREATE TABLE IF NOT EXISTS keystore (
				Key VARCHAR(32) NOT NULL,
				Value VARCHAR(200) NOT NULL,
				UNIQUE (Key)
			)
		'''
		# 'subreddits': '''
		# 	CREATE TABLE IF NOT EXISTS subreddits (
		# 		Subreddit VARCHAR(80) NOT NULL,
		# 		Banned BOOLEAN NOT NULL,
		# 		BanChecked TIMESTAMP NULL,
		# 		UNIQUE (Subreddit)
		# 	)
		# '''
	}

	def __init__(self, debug=False, publish=False, clone=False):
		if debug:
			if clone:
				if os.path.exists(static.DATABASE_DEBUG_NAME):
					os.remove(static.DATABASE_DEBUG_NAME)
				copyfile(static.DATABASE_NAME, static.DATABASE_DEBUG_NAME)

			self.dbConn = sqlite3.connect(static.DATABASE_DEBUG_NAME)
		else:
			self.dbConn = sqlite3.connect(static.DATABASE_NAME)

		c = self.dbConn.cursor()
		if publish or (debug and not clone):
			for table in Database.tables:
				c.execute(f"DROP TABLE IF EXISTS {table}")

		for table in Database.tables:
			c.execute(Database.tables[table])

		if self.get_keystore("remindme_comment") is None:
			self.update_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

		self.dbConn.commit()

	def close(self):
		self.dbConn.commit()
		self.dbConn.close()

	def save_reminder(self, reminder):
		if not isinstance(reminder, Reminder):
			return False

		c = self.dbConn.cursor()
		if reminder.db_id is not None:
			log.debug(f"Updating reminder: {reminder.db_id}")
			try:
				c.execute('''
					UPDATE reminders
					SET Source = ?,
						RequestedDate = ?,
						TargetDate = ?,
						Message = ?,
						User = ?,
						CommentId = ?
					WHERE ID = ?
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.comment_id,
					reminder.db_id))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to update reminder: {err}")
				return False
		else:
			log.debug("Saving new reminder")
			try:
				c.execute('''
					INSERT INTO reminders
					(Source, RequestedDate, TargetDate, Message, User, CommentId)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.comment_id))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to save reminder: {err}")
				return False

			if c.lastrowid is not None:
				reminder.db_id = c.lastrowid
				log.debug(f"Saved to: {reminder.db_id}")

		self.dbConn.commit()

		return True

	def get_pending_reminders(self):
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, CommentId
			FROM reminders
			WHERE TargetDate < CURRENT_TIMESTAMP
			'''):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				comment_id=row[6]
			)
			results.append(reminder)

		return results

	def get_user_reminders(self, username):
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, CommentId
			FROM reminders
			WHERE User = ?
			''', (username,)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				comment_id=row[6]
			)
			results.append(reminder)

		return results

	def get_reminder(self, reminder_id):
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, CommentId
			FROM reminders
			WHERE ID = ?
			''', (reminder_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			return None

		reminder = Reminder(
			source=result[1],
			target_date=utils.parse_datetime_string(result[3]),
			message=result[4],
			user=result[5],
			db_id=result[0],
			requested_date=utils.parse_datetime_string(result[2]),
			comment_id=result[6]
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

	def save_comment(self, db_comment):
		if not isinstance(db_comment, DbComment):
			return False

		c = self.dbConn.cursor()
		if db_comment.db_id is not None:
			log.debug(f"Updating comment: {db_comment.db_id}")
			try:
				c.execute('''
					UPDATE comments
					SET ThreadID = ?,
						ReminderId = ?,
						CurrentCount = ?,
						Source = ?
					WHERE ID = ?
				''', (
					db_comment.thread_id,
					db_comment.reminder_id,
					db_comment.current_count,
					db_comment.source,
					db_comment.db_id))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to update reminder: {err}")
				return False
		else:
			log.debug("Saving new comment")
			try:
				c.execute('''
					INSERT INTO comments
					(ThreadID, ReminderId, CurrentCount, Source)
					VALUES (?, ?, ?, ?)
				''', (
					db_comment.thread_id,
					db_comment.reminder_id,
					db_comment.current_count,
					db_comment.source))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to save comment: {err}")
				return False

			if c.lastrowid is not None:
				db_comment.db_id = c.lastrowid
				log.debug(f"Saved to: {db_comment.db_id}")

		self.dbConn.commit()

		return True

	def get_comment_in_thread(self, thread_id):
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, ThreadID, ReminderId, CurrentCount, Source
			FROM comments
			WHERE ThreadID = ?
			''', (thread_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			return None

		db_comment = DbComment(
			thread_id=result[1],
			reminder_id=result[2],
			source=result[4],
			current_count=result[3],
			db_id=result[0]
		)

		return db_comment

	def delete_comment(self, db_comment):
		if db_comment.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM comments
			WHERE ID = ?
		''', (db_comment.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			return True
		else:
			return False

	def save_keystore(self, key, value):
		c = self.dbConn.cursor()
		try:
			c.execute('''
				INSERT INTO keystore
				(Key, Value)
				VALUES (?, ?)
			''', (key, value))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save keystore: {err}")
			return False

		self.dbConn.commit()

		return True

	def update_keystore(self, key, value):
		c = self.dbConn.cursor()
		try:
			c.execute('''
				UPDATE keystore
				SET Value = ?
				WHERE Key = ?
			''', (value, key))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to update keystore: {err}")
			return False

		self.dbConn.commit()

		return True

	def get_keystore(self, key):
		c = self.dbConn.cursor()
		c.execute('''
			SELECT Value
			FROM keystore
			WHERE Key = ?
			''', (key,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			return None

		return result[0]

	def delete_keystore(self, key):
		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM keystore
			WHERE Key = ?
		''', (key,))
		self.dbConn.commit()

		if c.rowcount == 1:
			return True
		else:
			return False

	# def ban_subreddit(self, subreddit):
	# 	c = self.dbConn.cursor()
	# 	c.execute('''
	# 		SELECT Banned
	# 		FROM subreddits
	# 		WHERE Subreddit = ?
	# 		''', (subreddit,))
	#
	# 	result = c.fetchone()
	# 	if result is None or len(result) == 0:
	# 		try:
	# 			c.execute('''
	# 				INSERT INTO subreddits
	# 				(Subreddit, Banned, BanChecked)
	# 				VALUES (?, ?, ?)
	# 			''', (subreddit, True, utils.get_datetime_string(utils.datetime_now())))
	# 		except sqlite3.IntegrityError as err:
	# 			log.warning(f"Failed to ban subreddit: {err}")
	# 			return False
	# 	else:
	# 		try:
	# 			c.execute('''
	# 				UPDATE subreddits
	# 				SET Banned = ?
	# 					,BanChecked = ?
	# 				WHERE Subreddit = ?
	# 			''', (value, key))
	# 		except sqlite3.IntegrityError as err:
	# 			log.warning(f"Failed to update keystore: {err}")
	# 			return False

