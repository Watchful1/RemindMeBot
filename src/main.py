#!/usr/bin/python3

import logging.handlers
import sys
import signal
import time
import traceback
import discord_logging

log = discord_logging.init_logging()

import database_class
import static
import reddit_class
import messages
import comments
import notifications
import utils


remind_me_bot = None


def signal_handler(signal, frame):
	log.info("Handling interrupt")
	remind_me_bot.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class RemindMeBot:
	def __init__(self):
		self.once = False
		self.debug_db = False
		self.clone_db = False
		self.no_post = False
		self.user = None
		if len(sys.argv) >= 2:
			self.user = sys.argv[1]
			for arg in sys.argv:
				if arg == 'once':
					self.once = True
				elif arg == 'debug_db':
					self.debug_db = True
				elif arg == 'clone_db':
					self.clone_db = True
				elif arg == 'no_post':
					self.no_post = True
				elif arg == 'debug':
					discord_logging.set_level(logging.DEBUG)
		else:
			log.error("No user specified, aborting")
			raise ValueError

		discord_logging.init_discord_logging(self.user)

		self.reddit = reddit_class.Reddit(self.user, self.no_post)

		self.database = database_class.Database(debug=self.debug_db, clone=self.clone_db)

	def close(self):
		self.database.close()

	def process_messages(self):
		messages.process_messages(self.reddit, self.database)

	def process_comments(self):
		comments.process_comments(self.reddit, self.database)

	def send_notifications(self):
		notifications.send_reminders(self.reddit, self.database)
		notifications.send_cakeday_notifications(self.reddit, self.database)

	def backup_database(self):
		self.database.backup()


if __name__ == "__main__":
	remind_me_bot = RemindMeBot()

	last_backup = None
	while True:
		startTime = time.perf_counter()
		log.debug("Starting run")

		try:
			remind_me_bot.process_messages()
		except Exception as err:
			log.warning(f"Error processing messages: {err}")
			log.warning(traceback.format_exc())

		try:
			remind_me_bot.process_comments()
		except Exception as err:
			log.warning(f"Error processing comments: {err}")
			log.warning(traceback.format_exc())

		try:
			remind_me_bot.send_notifications()
		except Exception as err:
			log.warning(f"Error sending notifications: {err}")
			log.warning(traceback.format_exc())

		if utils.time_offset(last_backup, hours=24):
			try:
				remind_me_bot.backup_database()
				last_backup = utils.datetime_now()
			except Exception as err:
				log.warning(f"Error backing up database: {err}")
				log.warning(traceback.format_exc())

		log.debug("Run complete after: %d", int(time.perf_counter() - startTime))

		if remind_me_bot.once:
			break
		time.sleep(static.LOOP_TIME)
