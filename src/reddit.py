import logging.handlers
import praw
import configparser
import traceback

import globals

log = logging.getLogger("bot")
reddit = None


def init(user):
	global reddit

	try:
		reddit = praw.Reddit(
			user,
			user_agent=globals.USER_AGENT)
	except configparser.NoSectionError:
		log.error("User "+user+" not in praw.ini, aborting")
		return False

	globals.ACCOUNT_NAME = str(reddit.user.me()).lower()

	log.info("Logged into reddit as /u/" + globals.ACCOUNT_NAME)
	return True


def getMessages():
	return reddit.inbox.unread(limit=500)



