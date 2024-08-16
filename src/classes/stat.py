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
	initial_date = Column(UtcDateTime, nullable=False)
	count_reminders = Column(Integer, nullable=False)

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
		self.initial_date = utils.datetime_now()
