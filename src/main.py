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
		log.debug("Connecting to reddit")

		self.once = False
		self.debug = False
		self.user = None
		if len(sys.argv) >= 2:
			self.user = sys.argv[1]
			for arg in sys.argv:
				if arg == 'once':
					self.once = True
				elif arg == 'debug':
					self.debug = True
		else:
			log.error("No user specified, aborting")
			raise ValueError

		self.reddit = reddit_class.Reddit(self.user)

		self.database = database_class.Database()

	def process_once(self):
		startTime = time.perf_counter()
		log.debug("Starting run")

		messages.process_messages(self.reddit, self.database)

		log.debug("Run complete after: %d", int(time.perf_counter() - startTime))


if __name__ == "__main__":
	remind_me_bot = RemindMeBot()

	while True:
		remind_me_bot.process_once()
		if remind_me_bot.once:
			break
		time.sleep(static.LOOP_TIME)
