import sqlite3
import discord_logging
from datetime import timedelta


import utils


log = discord_logging.get_logger()


class _DatabaseSubreddits:
	def __init__(self):
		self.dbConn = self.dbConn  # for pycharm linting

	def ban_subreddit(self, subreddit):
		log.debug(f"Banning subreddit: {subreddit}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT Banned
			FROM subreddits
			WHERE Subreddit = ?
			''', (subreddit,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			try:
				c.execute('''
					INSERT INTO subreddits
					(Subreddit, Banned, BanChecked)
					VALUES (?, ?, ?)
				''', (subreddit, True, utils.get_datetime_string(utils.datetime_now())))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to ban subreddit: {err}")
				return False
		else:
			try:
				c.execute('''
					UPDATE subreddits
					SET Banned = ?
						,BanChecked = ?
					WHERE Subreddit = ?
				''', (True, utils.get_datetime_string(utils.datetime_now()), subreddit))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to update subreddit ban: {err}")
				return False

		self.dbConn.commit()
		return True

	def get_subreddit_banned(self, subreddit):
		log.debug(f"Getting subreddit ban: {subreddit}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT Banned
			FROM subreddits
			WHERE Subreddit = ?
				AND BanChecked > ?
			''', (subreddit, utils.get_datetime_string(utils.datetime_now() - timedelta(days=30))))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Not banned")
			return False

		log.debug(f"Value: {result[0] == 1}")
		return result[0] == 1
