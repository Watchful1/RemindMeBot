from sqlalchemy import Column, String, Integer
from database import Base


class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	timezone = Column(String(80))
	time_format = Column(String(80))
	recurring_sent = Column(Integer, nullable=False)

	def __init__(
		self,
		name,
		timezone=None,
		time_format=None,
		recurring_sent=0
	):
		self.name = name
		self.timezone = timezone
		self.time_format = time_format
		self.recurring_sent = recurring_sent
