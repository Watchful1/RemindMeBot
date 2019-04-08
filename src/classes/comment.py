import logging


log = logging.getLogger("bot")


class DbComment:
	def __init__(
		self,
		thread_id,
		comment_id,
		user,
		target_date,
		current_count=1,
		db_id=None
	):
		self.thread_id = thread_id
		self.comment_id = comment_id
		self.user = user
		self.target_date = target_date
		self.current_count = current_count
		self.db_id = db_id
