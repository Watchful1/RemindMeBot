import discord_logging
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from classes.comment import DbComment
from classes.reminder import Reminder

log = discord_logging.get_logger()


class _DatabaseComments:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def save_comment(self, db_comment):
		log.debug("Saving new comment")
		self.session.add(db_comment)

	def get_comment_by_thread(self, thread_id):
		log.debug(f"Fetching comment for thread: {thread_id}")

		return self.session.query(DbComment).filter_by(thread_id=thread_id).first()

	def delete_comment(self, db_comment):
		log.debug(f"Deleting comment by id: {db_comment.id}")
		self.session.delete(db_comment)

	def get_pending_incorrect_comments(self):
		log.debug("Fetching count of incorrect comments")

		Reminder1 = aliased(Reminder)
		Reminder2 = aliased(Reminder)
		subquery = self.session.query(Reminder1.id, func.count('*').label("new_count"))\
			.join(Reminder2, Reminder1.source == Reminder2.message)\
			.group_by(Reminder1.id)\
			.subquery()
		count = self.session.query(DbComment)\
			.join(subquery, DbComment.reminder_id == subquery.c.id)\
			.filter(subquery.c.new_count != DbComment.current_count)\
			.count()
		log.debug(f"Incorrect comments: {count}")
		return count

	def get_incorrect_comments(self, count):
		log.debug(f"Fetching incorrect comments")

		Reminder1 = aliased(Reminder)
		Reminder2 = aliased(Reminder)

		subquery = self.session.query(Reminder1, func.count('*').label("new_count"))\
			.join(Reminder2, Reminder1.source == Reminder2.message)\
			.group_by(Reminder1.id)\
			.subquery()

		Reminder3 = aliased(Reminder, subquery)

		results = self.session.query(DbComment, Reminder3, subquery.c.new_count)\
			.join(subquery, DbComment.reminder_id == subquery.c.id)\
			.filter(subquery.c.new_count != DbComment.current_count)\
			.limit(count)\
			.all()

		log.debug(f"Found incorrect comments: {len(results)}")
		return results

	def get_count_all_comments(self):
		return self.session.query(DbComment).count()
