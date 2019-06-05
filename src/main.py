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


def signal_handler(signal, frame):
	log.info("Handling interrupt")
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

		self.database = database_class.Database(self.debug_db, self.clone_db)

	def process_once(self):
		startTime = time.perf_counter()
		log.debug("Starting run")

		messages.process_messages(self.reddit, self.database)

		comments.process_comments(self.reddit, self.database)

		notifications.send_reminders(self.reddit, self.database)

		log.debug("Run complete after: %d", int(time.perf_counter() - startTime))


if __name__ == "__main__":
	remind_me_bot = RemindMeBot()

	while True:
		try:
			remind_me_bot.process_once()
		except Exception:
			log.warning("Error in main loop")
			log.warning(traceback.format_exc())
		if remind_me_bot.once:
			break
		time.sleep(static.LOOP_TIME)
