from sqlalchemy import Column, ForeignKey, Integer, String
from database_new import Base


class DbComment(Base):
	__tablename__ = 'comments'

	id = Column(Integer, primary_key=True)
	thread_id = Column(String(12))
	comment_id = Column(String(12))
	reminder_id = Column(Integer, ForeignKey('reminders.id'))
	user = Column(String(80))
	source = Column(String(400))
	current_count = Column(Integer)

	def __init__(
		self,
		thread_id,
		comment_id,
		reminder_id,
		user,
		source,
		current_count=0,
		db_id=None
	):
		self.thread_id = thread_id
		self.comment_id = comment_id
		self.reminder_id = reminder_id
		self.user = user
		self.source = source
		self.current_count = current_count
		self.db_id = db_id
