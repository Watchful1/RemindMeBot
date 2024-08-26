from sqlalchemy import Column, ForeignKey, Integer, String
from database import Base
from database.UtcDateTime import UtcDateTime

import utils


class DbStat(Base):
	__tablename__ = 'stats'

	id = Column(Integer, primary_key=True)
	subreddit = Column(String(80), nullable=False)
	thread_id = Column(String(12), nullable=False)
	comment_id = Column(String(12))
	initial_date = Column(UtcDateTime)
	count_reminders = Column(Integer, nullable=False)
	#thread_title = Column(String(200))

	title = None
	answered = False
	count_pending_reminders = None

	def __init__(
		self,
		subreddit,
		thread_id,
		comment_id,
		count_reminders=1
	):
		self.subreddit = subreddit
		self.thread_id = thread_id
		self.comment_id = comment_id
		self.count_reminders = count_reminders

	def __str__(self):
		return f"{self.id}:{self.subreddit}:{self.thread_id}:{self.comment_id}:" \
			f": {utils.get_datetime_string(self.initial_date)}:{self.count_reminders}"
