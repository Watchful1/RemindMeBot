from sqlalchemy import Column, ForeignKey, Integer, String
from database import Base


class DbComment(Base):
	__tablename__ = 'comments'

	id = Column(Integer, primary_key=True)
	thread_id = Column(String(12), nullable=False)
	comment_id = Column(String(12), nullable=False)
	reminder_id = Column(Integer, ForeignKey('reminders.id'), nullable=False)
	user = Column(String(80), nullable=False)
	source = Column(String(400), nullable=False)
	current_count = Column(Integer, nullable=False)

	def __init__(
		self,
		thread_id,
		comment_id,
		reminder_id,
		user,
		source,
		current_count=0
	):
		self.thread_id = thread_id
		self.comment_id = comment_id
		self.reminder_id = reminder_id
		self.user = user
		self.source = source
		self.current_count = current_count
