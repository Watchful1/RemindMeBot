from sqlalchemy import Column, Integer, String, Boolean, func
from database.UtcDateTime import UtcDateTime
from database import Base


class Subreddit(Base):
	__tablename__ = 'subreddits'

	subreddit = Column(String(80), primary_key=True)
	banned = Column(Boolean, nullable=False)
	ban_checked = Column(UtcDateTime, nullable=False)

	def __init__(
		self,
		subreddit,
		banned,
		ban_checked
	):
		self.subreddit = subreddit
		self.banned = banned
		self.ban_checked = ban_checked
