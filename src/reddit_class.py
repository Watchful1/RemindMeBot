import logging.handlers
import praw
import configparser
import traceback

import static

log = logging.getLogger("bot")


class Reddit:
	def __init__(self, user, no_post):
		self.no_post = no_post
		try:
			self.reddit = praw.Reddit(
				user,
				user_agent=static.USER_AGENT)
		except configparser.NoSectionError:
			log.error("User "+user+" not in praw.ini, aborting")
			raise ValueError
		static.ACCOUNT_NAME = self.reddit.user.me().name
		log.info("Logged into reddit as /u/" + static.ACCOUNT_NAME)

	def get_messages(self):
		return self.reddit.inbox.unread(limit=500)

	def reply_message(self, message, body):
		if self.no_post:
			log.info(body)
		else:
			message.reply(body)

	def reply_comment(self, comment, body):
		if self.no_post:
			log.info(body)
			return "xxxxxx"
		else:
			return comment.reply(body)

	def get_comment(self, comment_id):
		return self.reddit.comment(comment_id)

	def comment_exists(self, comment):
		try:
			comment._fetch()
		except praw.exceptions.PRAWException:
			return False
		return True

	def get_comment_parent(self, comment):
		return comment.parent()

	def delete_comment(self, comment):
		if not self.no_post:
			comment.delete()
