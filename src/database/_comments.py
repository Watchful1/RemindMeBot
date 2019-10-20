import discord_logging

from classes.comment import DbComment

log = discord_logging.get_logger()


class _DatabaseComments:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def save_comment(self, db_comment):
		if db_comment.id is None:
			log.debug("Saving new comment")
		else:
			log.debug(f"Updating comment: {db_comment.id}")
		try:
			self.session.merge(db_comment)
		except:
			return False
		return True

	def get_comment_by_thread(self, thread_id):
		log.debug(f"Fetching comment for thread: {thread_id}")

		return self.session.query(DbComment).filter_by(thread_id=thread_id).first()

	def delete_comment(self, db_comment):
		log.debug(f"Deleting comment by id: {db_comment.id}")
		self.session.delete(db_comment)

	def get_pending_incorrect_comments(self):
		log.debug("Fetching count of incorrect comments")
		log.debug(f"Incorrect comments: {0}")
		return None

	def get_incorrect_comments(self, count):
		log.debug(f"Fetching incorrect comments")
		log.debug(f"Found incorrect comments: {0}")
		return []
