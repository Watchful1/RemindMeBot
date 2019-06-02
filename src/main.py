#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import signal
import time
import traceback

import database_class
import static
import reddit_class
import messages
import comments
import notifications

LOG_LEVEL = logging.DEBUG


LOG_FOLDER_NAME = "logs"
if not os.path.exists(LOG_FOLDER_NAME):
	os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 1024 * 16

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(
		LOG_FILENAME,
	    maxBytes=LOG_FILE_MAXSIZE,
	     backupCount=LOG_FILE_BACKUPCOUNT)
	log_fileHandler.setFormatter(log_formatter)
	log.addHandler(log_fileHandler)


def signal_handler(signal, frame):
	log.info("Handling interupt")
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
					log.setLevel(logging.DEBUG)
		else:
			log.error("No user specified, aborting")
			raise ValueError

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
