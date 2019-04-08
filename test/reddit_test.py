import logging.handlers

import static
import utils

log = logging.getLogger("bot")


class User:
	def __init__(self, name):
		self.name = name


class RedditObject:
	def __init__(
		self,
		body=None,
		author=None,
		created=None,
		id=None
	):
		self.body = body
		if author is None:
			self.author = author
		else:
			self.author = User(author)
		if id is None:
			self.id = utils.random_id()
		else:
			self.id = id
		self.fullname = "t4_"+self.id
		if created is None:
			self.created_utc = utils.datetime_now().timestamp()
		else:
			self.created_utc = created.timestamp()

		self.parent = None
		self.children = []

	def get_first_child(self):
		if len(self.children):
			return self.children[0]
		else:
			return None

	def mark_read(self):
		return

	def reply(self, body):
		new_message = RedditObject(body, static.ACCOUNT_NAME)
		new_message.parent = self
		self.children.append(new_message)
		return new_message


class Reddit:
	def __init__(self, user):
		static.ACCOUNT_NAME = user
		self.sent_messages = []
		self.self_comments = []
		self.all_comments = {}

	def add_comment(self, comment, self_comment=False):
		self.all_comments[comment.id] = comment
		if self_comment:
			self.self_comments.append(comment)

	def reply_message(self, message, body):
		self.sent_messages.append(message.reply(body))

	def reply_comment(self, comment, body):
		new_comment = comment.reply(body)
		self.add_comment(comment, True)
		return new_comment

	def get_comment(self, comment_id):
		if comment_id in self.all_comments:
			return self.all_comments[comment_id]
		else:
			return RedditObject(id=comment_id)

	def delete_comment(self, comment):
		if comment.id in self.all_comments:
			del self.all_comments[comment.id]
		try:
			self.self_comments.remove(comment)
		except ValueError:
			pass

		if comment.parent is not None:
			try:
				comment.parent.children.remove(comment)
			except ValueError:
				pass

		for child in comment.children:
			child.parent = None

		return True
