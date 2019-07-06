import sqlite3
import discord_logging
import os
from shutil import copyfile

import static
import utils
from ._reminders import _DatabaseReminders
from ._comments import _DatabaseComments
from ._keystore import _DatabaseKeystore


log = discord_logging.get_logger()


class Database(_DatabaseReminders, _DatabaseComments, _DatabaseKeystore):
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
		_DatabaseReminders.__init__(self)
		_DatabaseComments.__init__(self)
		_DatabaseKeystore.__init__(self)

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

