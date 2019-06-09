import sqlite3
import discord_logging
import os
from shutil import copyfile
from datetime import datetime
from datetime import timedelta

from classes.reminder import Reminder
from classes.comment import DbComment
from classes.cakeday import Cakeday
import static
import utils


log = discord_logging.get_logger()


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
				Defaulted BOOLEAN NOT NULL
			)
		''',
		'comments': '''
			CREATE TABLE IF NOT EXISTS comments (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				ThreadID VARCHAR(12) NOT NULL,
				CommentID VARCHAR(12) NOT NULL,
				ReminderId INTEGER NOT NULL,
				CurrentCount INTEGER DEFAULT 1,
				User VARCHAR(80) NOT NULL,
				Source VARCHAR(400) NOT NULL,
				UNIQUE (ThreadID)
			)
		''',
		'cakedays': '''
			CREATE TABLE IF NOT EXISTS cakedays (
				ID INTEGER PRIMARY KEY AUTOINCREMENT,
				CakedayDate TIMESTAMP NOT NULL,
				User VARCHAR(80) NOT NULL,
				UNIQUE (User)
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
		log.info(f"Initializing database class: debug={debug} publish={publish} clone={clone}")
		self.debug = debug
		self.dbConn = None
		self.init(debug, publish, clone)

	def init(self, debug, publish, clone):
		if debug:
			if clone:
				if os.path.exists(static.DATABASE_DEBUG_NAME):
					os.remove(static.DATABASE_DEBUG_NAME)
				copyfile(static.DATABASE_NAME, static.DATABASE_DEBUG_NAME)

			self.dbConn = sqlite3.connect(static.DATABASE_DEBUG_NAME)
		else:
			self.dbConn = sqlite3.connect(static.DATABASE_NAME)

		c = self.dbConn.cursor()
		if publish:
			for table in Database.tables:
				c.execute(f"DROP TABLE IF EXISTS {table}")

		for table in Database.tables:
			c.execute(Database.tables[table])

		if self.get_keystore("remindme_comment") is None:
			self.save_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

		self.dbConn.commit()

	def close(self, silent=False):
		if not silent:
			log.debug("Closing database")
		self.dbConn.commit()
		self.dbConn.close()

	def backup(self):
		log.info("Backing up database")
		self.close(True)

		if not os.path.exists(static.BACKUP_FOLDER_NAME):
			os.makedirs(static.BACKUP_FOLDER_NAME)
		copyfile(
			static.DATABASE_NAME,
			static.BACKUP_FOLDER_NAME + "/" + utils.datetime_now().strftime("%Y-%m-%d_%H-%M") + ".db")

		self.init(self.debug, False, False)

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
						Defaulted = ?
					WHERE ID = ?
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.defaulted,
					reminder.db_id))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to update reminder: {err}")
				return False
		else:
			log.debug("Saving new reminder")
			try:
				c.execute('''
					INSERT INTO reminders
					(Source, RequestedDate, TargetDate, Message, User, Defaulted)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.defaulted))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to save reminder: {err}")
				return False

			if c.lastrowid is not None:
				reminder.db_id = c.lastrowid
				log.debug(f"Saved to: {reminder.db_id}")

		self.dbConn.commit()

		return True

	def get_count_pending_reminders(self, timestamp):
		log.debug("Fetching count of pending reminders")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT COUNT(*)
			FROM reminders
			WHERE TargetDate < ?
			''', (utils.get_datetime_string(timestamp),))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No pending reminders")
			return 0

		log.debug(f"Count reminders: {result[0]}")
		return result[0]

	def get_pending_reminders(self, count, timestamp):
		log.debug("Fetching pending reminders")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, Defaulted
			FROM reminders
			WHERE TargetDate < ?
			ORDER BY TargetDate ASC
			LIMIT ?
			''', (utils.get_datetime_string(timestamp), count)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				defaulted=row[6] == 1
			)
			results.append(reminder)

		log.debug(f"Found reminders: {len(results)}")
		return results

	def get_user_reminders(self, username):
		log.debug(f"Fetching reminders for u/{username}")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, Defaulted
			FROM reminders
			WHERE User = ?
			ORDER BY TargetDate ASC
			''', (username,)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				defaulted=row[6] == 1
			)
			results.append(reminder)

		log.debug(f"Found reminders: {len(results)}")
		return results

	def get_reminder(self, reminder_id):
		log.debug(f"Fetching reminder by id: {reminder_id}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, Source, RequestedDate, TargetDate, Message, User, Defaulted
			FROM reminders
			WHERE ID = ?
			''', (reminder_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Reminder not found")
			return None

		reminder = Reminder(
			source=result[1],
			target_date=utils.parse_datetime_string(result[3]),
			message=result[4],
			user=result[5],
			db_id=result[0],
			requested_date=utils.parse_datetime_string(result[2]),
			defaulted=result[6] == 1
		)

		return reminder

	def delete_reminder(self, reminder):
		log.debug(f"Deleting reminder by id: {reminder.db_id}")
		if reminder.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM reminders
			WHERE ID = ?
		''', (reminder.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Reminder deleted")
			return True
		else:
			log.debug("Reminder not deleted")
			return False

	def delete_user_reminders(self, user):
		log.debug(f"Deleting all reminders for u/{user}")
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
						CommentID = ?,
						ReminderId = ?,
						CurrentCount = ?,
						User=?,
						Source = ?
					WHERE ID = ?
				''', (
					db_comment.thread_id,
					db_comment.comment_id,
					db_comment.reminder_id,
					db_comment.current_count,
					db_comment.user,
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
					(ThreadID, CommentID, ReminderId, CurrentCount, User, Source)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (
					db_comment.thread_id,
					db_comment.comment_id,
					db_comment.reminder_id,
					db_comment.current_count,
					db_comment.user,
					db_comment.source))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to save comment: {err}")
				return False

			if c.lastrowid is not None:
				db_comment.db_id = c.lastrowid
				log.debug(f"Saved to: {db_comment.db_id}")

		self.dbConn.commit()

		return True

	def get_comment_by_thread(self, thread_id):
		log.debug(f"Fetching comment for thread: {thread_id}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, ThreadID, CommentID, ReminderId, CurrentCount, User, Source
			FROM comments
			WHERE ThreadID = ?
			''', (thread_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No comment found")
			return None

		db_comment = DbComment(
			thread_id=result[1],
			comment_id=result[2],
			reminder_id=result[3],
			user=result[5],
			source=result[6],
			current_count=result[4],
			db_id=result[0]
		)

		return db_comment

	def delete_comment(self, db_comment):
		log.debug(f"Deleting comment by id: {db_comment.db_id}")
		if db_comment.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM comments
			WHERE ID = ?
		''', (db_comment.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Comment deleted")
			return True
		else:
			log.debug("Comment not deleted")
			return False

	def get_pending_incorrect_comments(self):
		log.debug("Fetching count of incorrect comments")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT count(*)
			FROM comments cm
			LEFT JOIN
				(
					SELECT rm1.ID,
						   count(*) as NewCount
					FROM reminders rm1
						INNER JOIN reminders rm2
							ON rm1.Source = rm2.Message
					GROUP BY rm1.ID
				) AS rm
					ON cm.ReminderId = rm.ID
			WHERE rm.NewCount != cm.CurrentCount
			''')

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No incorrect comments")
			return 0

		log.debug(f"Incorrect comments: {result[0]}")
		return result[0]

	def get_incorrect_comments(self, count):
		log.debug(f"Fetching incorrect comments")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT cm.ID,
				cm.ThreadID,
				cm.CommentID,
				cm.ReminderId,
				cm.CurrentCount,
				cm.User,
				cm.Source,
				rm.ID,
				rm.Source,
				rm.RequestedDate,
				rm.TargetDate,
				rm.Message,
				rm.User,
				rm.Defaulted,
				rm.NewCount
			FROM comments cm
			LEFT JOIN
				(
					SELECT rm1.ID,
						rm1.Source,
						rm1.RequestedDate,
						rm1.TargetDate,
						rm1.Message,
						rm1.User,
						count(*) as NewCount
					FROM reminders rm1
						INNER JOIN reminders rm2
							ON rm1.Source = rm2.Message
					GROUP BY rm1.ID
				) AS rm
					ON cm.ReminderId = rm.ID
			WHERE rm.NewCount != cm.CurrentCount
			LIMIT ?
			''', (count,)):
			db_comment = DbComment(
				thread_id=row[1],
				comment_id=row[2],
				reminder_id=row[3],
				user=row[5],
				source=row[6],
				current_count=row[4],
				db_id=row[0]
			)
			reminder = Reminder(
				source=row[8],
				target_date=utils.parse_datetime_string(row[10]),
				message=row[11],
				user=row[12],
				db_id=row[7],
				requested_date=utils.parse_datetime_string(row[9]),
				count_duplicates=row[14],
				thread_id=row[1],
				defaulted=row[13] == 1
			)
			results.append((db_comment, reminder))

		log.debug(f"Found incorrect comments: {len(results)}")
		return results

	def add_cakeday(self, cakeday):
		if cakeday.db_id is not None:
			log.warning(f"This cakeday already exists: {cakeday.db_id}")

		c = self.dbConn.cursor()
		log.debug("Saving new cakeday")
		try:
			c.execute('''
				INSERT INTO cakedays
				(CakedayDate, User)
				VALUES (?, ?)
			''', (
				utils.get_datetime_string(cakeday.date_time),
				cakeday.user))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save cakeday: {err}")
			return False

		if c.lastrowid is not None:
			cakeday.db_id = c.lastrowid
			log.debug(f"Saved to: {cakeday.db_id}")

		self.dbConn.commit()

		return True

	def delete_cakeday(self, cakeday):
		log.debug(f"Deleting cakeday by id: {cakeday.db_id}")
		if cakeday.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM cakedays
			WHERE ID = ?
		''', (cakeday.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Cakeday deleted")
			return True
		else:
			log.debug("Cakeday not deleted")
			return False

	def bump_cakeday(self, cakeday):
		if cakeday.db_id is None:
			log.warning(f"This cakeday doesn't exist: {cakeday.user}")

		c = self.dbConn.cursor()
		log.debug("Bumping cakeday one year")
		try:
			c.execute('''
				UPDATE cakedays
				SET CakedayDate = ?
				WHERE ID = ?
			''', (
				utils.get_datetime_string(utils.add_years(cakeday.date_time, 1)),
				cakeday.db_id))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to bump cakeday: {err}")
			return False

		self.dbConn.commit()

		return True

	def get_cakeday(self, user):
		log.debug(f"Fetching cake by user: {user}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, CakedayDate, User
			FROM cakedays
			WHERE User = ?
			''', (user,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Cakeday not found")
			return None

		cakeday = Cakeday(
			user=result[2],
			date_time=utils.parse_datetime_string(result[1]),
			db_id=result[0]
		)

		return cakeday

	def get_count_pending_cakedays(self, timestamp):
		log.debug("Fetching count of pending cakedays")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT COUNT(*)
			FROM cakedays
			WHERE CakedayDate < ?
			''', (utils.get_datetime_string(timestamp),))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No pending cakedays")
			return 0

		log.debug(f"Count cakedays: {result[0]}")
		return result[0]

	def get_pending_cakedays(self, count, timestamp):
		log.debug("Fetching pending cakedays")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, CakedayDate, User
			FROM cakedays
			WHERE CakedayDate < ?
			ORDER BY CakedayDate ASC
			LIMIT ?
			''', (utils.get_datetime_string(timestamp), count)):
			cakeday = Cakeday(
				user=row[2],
				date_time=utils.parse_datetime_string(row[1]),
				db_id=row[0]
			)
			results.append(cakeday)

		log.debug(f"Found cakedays: {len(results)}")
		return results

	def save_keystore(self, key, value):
		log.debug(f"Saving keystore: {key} : {value}")
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
		log.debug(f"Updating keystore: {key} : {value}")
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
		log.debug(f"Fetching keystore: {key}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT Value
			FROM keystore
			WHERE Key = ?
			''', (key,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Key not found")
			return None

		log.debug(f"Value: {result[0]}")
		return result[0]

	def delete_keystore(self, key):
		log.debug(f"Deleting key: {key}")
		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM keystore
			WHERE Key = ?
		''', (key,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Key deleted")
			return True
		else:
			log.debug("Key not deleted")
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

