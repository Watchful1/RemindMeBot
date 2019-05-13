import logging


log = logging.getLogger("bot")


class DbComment:
	def __init__(
		self,
		thread_id,
		reminder_id,
		source,
		current_count=1,
		db_id=None
	):
		self.thread_id = thread_id
		self.reminder_id = reminder_id
		self.source = source
		self.current_count = current_count
		self.db_id = db_id
