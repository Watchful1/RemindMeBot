from sqlalchemy import Column, ForeignKey, Integer, String
from database_new import Base


class KeyValue(Base):
	__tablename__ = 'key_value'

	key = Column(String(32), primary_key=True)
	value = Column(String(200))
