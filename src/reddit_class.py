import discord_logging
import praw
import prawcore
import configparser
import traceback
import requests
from datetime import timedelta

import static
import utils
from classes.queue import Queue
from classes.enums import ReturnType


log = discord_logging.get_logger()


class Reddit:
	def __init__(self, user_name, no_post):
		log.info(f"Initializing reddit class: user={user_name} no_post={no_post}")
		self.no_post = no_post
		try:
			self.reddit = praw.Reddit(
				user_name,
				user_agent=static.USER_AGENT)
		except configparser.NoSectionError:
			log.error("User "+user_name+" not in praw.ini, aborting")
			raise ValueError
		static.ACCOUNT_NAME = self.reddit.user.me().name
		log.info("Logged into reddit as /u/" + static.ACCOUNT_NAME)

		self.processed_comments = Queue(100)
		self.consecutive_timeouts = 0
		self.timeout_warn_threshold = 1

	def run_function(self, function, arguments):
		output = None
		result = None
		try:
			output = function(*arguments)
		except praw.exceptions.APIException as err:
			for return_type in ReturnType:
				if err.error_type == return_type.name:
					result = return_type
					break
			if result is None:
				raise
		except prawcore.exceptions.Forbidden:
			result = ReturnType.FORBIDDEN
		except IndexError:
			result = ReturnType.QUARANTINED

		if result is None:
			result = ReturnType.SUCCESS
		return output, result

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
			return ReturnType.SUCCESS
		else:
			output, result = self.run_function(message.reply, [body])
			return result

	def mark_read(self, message):
		log.debug(f"Marking message as read: {message.id}")
		if not self.no_post:
			message.mark_read()

	def reply_comment(self, comment, body):
		log.debug(f"Replying to message: {comment.id}")
		if self.no_post:
			log.info(body)
			return "xxxxxx", ReturnType.SUCCESS
		else:
			output, result = self.run_function(comment.reply, [body])
			if output is not None:
				return output.id, result
			else:
				return None, result

	def send_message(self, user_name, subject, body):
		log.debug(f"Sending message to u/{user_name}")
		if self.no_post:
			log.info(body)
			return ReturnType.SUCCESS
		else:
			redditor = self.reddit.redditor(user_name)
			output, result = self.run_function(redditor.message, [subject, body])
			return result

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
			output, result = self.run_function(comment.edit, [body])
			return result

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

	def quarantine_opt_in(self, subreddit_name):
		log.debug(f"Opting in to subreddit: {subreddit_name}")
		if not self.no_post:
			try:
				self.reddit.subreddit(subreddit_name).quaran.opt_in()
			except Exception:
				log.warning(f"Error opting in to subreddit: {subreddit_name}")
				log.warning(traceback.format_exc())
				return False
		return True

	def get_user_creation_date(self, user_name):
		log.debug(f"Getting user creation date: {user_name}")
		try:
			return self.reddit.user(user_name).created_utc
		except Exception:
			return None

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

			if self.timeout_warn_threshold > 1:
				log.warning(f"Recovered from timeouts after {self.consecutive_timeouts} attempts")

			self.consecutive_timeouts = 0
			self.timeout_warn_threshold = 1

		except requests.exceptions.ReadTimeout:
			self.consecutive_timeouts += 1
			if self.consecutive_timeouts >= pow(self.timeout_warn_threshold, 2) * 5:
				log.warning(f"{self.consecutive_timeouts} consecutive timeouts for search term: {keyword}")
				self.timeout_warn_threshold += 1
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
