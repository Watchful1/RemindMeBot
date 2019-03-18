from datetime import datetime


class Reminder:
	def __init__(self, source_id, target_date, message, user, db_id=None, requested_date=datetime.utcnow()):
		self.source_id = source_id
		self.target_date = target_date
		self.message = message
		self.user = user

		self.requested_date = requested_date
		self.db_id = db_id
