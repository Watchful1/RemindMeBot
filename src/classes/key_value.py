from sqlalchemy import Column, ForeignKey, Integer, String
from database import Base


class KeyValue(Base):
	__tablename__ = 'key_value'

	key = Column(String(32), primary_key=True)
	value = Column(String(200))

	def __init__(
		self,
		key,
		value
	):
		self.key = key
		self.value = value
