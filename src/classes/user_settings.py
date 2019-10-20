from sqlalchemy import Column, String
from database import Base


class UserSettings(Base):
	__tablename__ = 'user_settings'

	user = Column(String(80), primary_key=True)
	timezone = Column(String(80))

	def __init__(
		self,
		user,
		timezone=None
	):
		self.user = user
		self.timezone = timezone
