from sqlalchemy import Column, String, Integer
from database import Base


class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	timezone = Column(String(80))

	def __init__(
		self,
		name,
		timezone=None
	):
		self.name = name
		self.timezone = timezone
