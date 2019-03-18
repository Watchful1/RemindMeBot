import logging.handlers
import praw
import configparser
import traceback

import globals

log = logging.getLogger("bot")


class Reddit:
	def __init__(self, user):
		try:
			self.reddit = praw.Reddit(
				user,
				user_agent=globals.USER_AGENT)
		except configparser.NoSectionError:
			log.error("User "+user+" not in praw.ini, aborting")
			self.reddit = None

		globals.ACCOUNT_NAME = self.reddit.user.me().name.lower()

		log.info("Logged into reddit as /u/" + globals.ACCOUNT_NAME)

	def get_messages(self):
		return self.reddit.inbox.unread(limit=500)



