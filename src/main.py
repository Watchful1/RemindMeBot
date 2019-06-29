#!/usr/bin/python3

import logging.handlers
import sys
import signal
import time
import traceback
import discord_logging
import argparse

log = discord_logging.init_logging()

import database_class
import static
import reddit_class
import messages
import comments
import notifications
import utils


database = None


def signal_handler(signal, frame):
	log.info("Handling interrupt")
	database.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Reddit RemindMe bot")
	parser.add_argument("user", help="The reddit user account to use")
	parser.add_argument("--once", help="Only run the loop once", action='store_const', const=True, default=False)
	parser.add_argument("--debug_db", help="Use the debug database", action='store_const', const=True, default=False)
	parser.add_argument(
		"--clone_db", help="Copy the primary database to the debug on", action='store_const', const=True, default=False)
	parser.add_argument(
		"--no_post", help="Print out reddit actions instead of posting to reddit", action='store_const', const=True,
		default=False)
	parser.add_argument(
		"--no_backup", help="Don't backup the database", action='store_const', const=True, default=False)
	parser.add_argument(
		"--reset_comment", help="Reset the last comment read timestamp", action='store_const', const=True,
		default=False)
	parser.add_argument("--debug", help="Set the log level to debug", action='store_const', const=True, default=False)
	args = parser.parse_args()

	if args.debug:
		discord_logging.set_level(logging.DEBUG)

	discord_logging.init_discord_logging(args.user, 1)
	reddit = reddit_class.Reddit(args.user, args.no_post)
	database = database_class.Database(debug=args.debug_db, clone=args.clone_db)
	if args.reset_comment:
		log.info("Resetting comment processed timestamp")
		database.update_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

	last_backup = None
	last_comments = None
	while True:
		startTime = time.perf_counter()
		log.debug("Starting run")

		actions = 0
		errors = 0

		try:
			actions += messages.process_messages(reddit, database)
		except Exception as err:
			log.warning(f"Error processing messages: {err}")
			log.warning(traceback.format_exc())
			errors += 1

		try:
			actions += comments.process_comments(reddit, database)
		except Exception as err:
			log.warning(f"Error processing comments: {err}")
			log.warning(traceback.format_exc())
			errors += 1

		try:
			actions += notifications.send_reminders(reddit, database)
			actions += notifications.send_cakeday_notifications(reddit, database)
		except Exception as err:
			log.warning(f"Error sending notifications: {err}")
			log.warning(traceback.format_exc())
			errors += 1

		if utils.time_offset(last_comments, minutes=30):
			try:
				comments.update_comments(reddit, database)
				last_comments = utils.datetime_now()
			except Exception as err:
				log.warning(f"Error updating comments: {err}")
				log.warning(traceback.format_exc())
				errors += 1

		if not args.no_backup and utils.time_offset(last_backup, hours=24):
			try:
				database.backup()
				last_backup = utils.datetime_now()
			except Exception as err:
				log.warning(f"Error backing up database: {err}")
				log.warning(traceback.format_exc())
				errors += 1

		log.debug("Run complete after: %d", int(time.perf_counter() - startTime))

		discord_logging.flush_discord()

		if args.once:
			break

		sleep_time = max(30 - actions, 0) + (30 * errors)
		log.debug(f"Sleeping {sleep_time}")

		time.sleep(sleep_time)
