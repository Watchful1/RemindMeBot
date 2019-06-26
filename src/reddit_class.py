import discord_logging
import praw
import configparser
import traceback
import requests
import time
from datetime import timedelta

import static
import utils
from classes.queue import Queue


log = discord_logging.get_logger()


# class DebugReddit(praw.Reddit):
# 	def __init__(
# 			self,
# 			site_name=None,
# 			requestor_class=None,
# 			requestor_kwargs=None,
# 			**config_settings):
# 		super(DebugReddit, self).__init__(site_name, requestor_class, requestor_kwargs, **config_settings)
# 		self.request_count = 0
#
# 	def request(self, method, path, params=None, data=None, files=None):
# 		self.request_count += 1
# 		return super(DebugReddit, self).request(method, path, params, data, files)


class Reddit:
	def __init__(self, user, no_post):
		log.info(f"Initializing reddit class: user={user} no_post={no_post}")
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

		self.processed_comments = Queue(100)
		self.consecutive_timeouts = 0

	def is_message(self, item):
		return isinstance(item, praw.models.Message)

	def get_messages(self, count=500):
		log.debug("Fetching unread messages")
		message_list = []
		for message in self.reddit.inbox.unread(limit=count):
			message_list.append(message)
		return message_list

	def reply_message(self, message, body):
		log.debug(f"Replying to message: {message.id}")
		if self.no_post:
			log.info(body)
		else:
			message.reply(body)

	def mark_read(self, message):
		log.debug(f"Marking message as read: {message.id}")
		if not self.no_post:
			message.mark_read()

	def reply_comment(self, comment, body):
		log.debug(f"Replying to message: {comment.id}")
		if self.no_post:
			log.info(body)
			return "xxxxxx"
		else:
			return comment.reply(body).id

	def send_message(self, username, subject, body):
		log.debug(f"Sending message to u/{username}")
		if self.no_post:
			log.info(body)
		else:
			self.reddit.redditor(username).message(subject, body)

	def get_comment(self, comment_id):
		log.debug(f"Fetching comment by id: {comment_id}")
		if comment_id == "xxxxxx":
			return None
		else:
			return self.reddit.comment(comment_id)

	def edit_comment(self, body, comment=None, comment_id=None):
		if comment is None:
			comment = self.get_comment(comment_id)
		log.debug(f"Editing comment: {comment.id}")

		if self.no_post:
			log.info(body)
		else:
			comment.edit(body)

	def delete_comment(self, comment):
		log.debug(f"Deleting comment: {comment.id}")
		if not self.no_post:
			try:
				comment.delete()
			except Exception:
				log.warning(f"Error deleting comment: {comment.comment_id}")
				log.warning(traceback.format_exc())
				return False
		return True

	def get_keyword_comments(self, keyword, last_seen):
		if not len(self.processed_comments.list):
			last_seen = last_seen + timedelta(seconds=1)

		log.debug(f"Fetching comments for keyword: {keyword} : {utils.get_datetime_string(last_seen)}")
		url = f"https://api.pushshift.io/reddit/comment/search?q={keyword}&limit=100&sort=desc"
		try:
			json = requests.get(url, headers={'User-Agent': static.USER_AGENT}, timeout=10)
			if json.status_code != 200:
				log.warning(f"Could not parse data for search term: {keyword} status: {str(json.status_code)}")
				return []
			comments = json.json()['data']

			self.consecutive_timeouts = 0

		except requests.exceptions.ReadTimeout:
			self.consecutive_timeouts += 1
			if self.consecutive_timeouts >= 5:
				log.warning(f"Five consecutive timeouts for search term: {keyword}")
				self.consecutive_timeouts = 0
			return []

		except Exception as err:
			log.warning(f"Could not parse data for search term: {keyword}")
			log.warning(traceback.format_exc())
			return []

		if not len(comments):
			log.warning(f"No comments found for search term: {keyword}")
			return []

		result_comments = []
		for comment in comments:
			date_time = utils.datetime_from_timestamp(comment['created_utc'])
			if last_seen > date_time:
				break

			if not self.processed_comments.contains(comment['id']):
				result_comments.append(comment)

		log.debug(f"Found comments: {len(result_comments)}")
		return result_comments

	def mark_keyword_comment_processed(self, comment_id):
		self.processed_comments.put(comment_id)
