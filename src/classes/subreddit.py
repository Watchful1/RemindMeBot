from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from database import Base


class Subreddit(Base):
	__tablename__ = 'subreddits'

	subreddit = Column(String(80), primary_key=True)
	banned = Column(Boolean, nullable=False)
	ban_checked = Column(DateTime, nullable=False, default=func.utc_timestamp())

	def __init__(
		self,
		subreddit,
		banned
	):
		self.subreddit = subreddit
		self.banned = banned
