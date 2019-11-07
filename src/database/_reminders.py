import discord_logging
from sqlalchemy.orm import joinedload

import static
from classes.reminder import Reminder
from classes.user import User

log = discord_logging.get_logger()


class _DatabaseReminders:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def add_reminder(self, reminder):
		log.debug("Saving new reminder")
		self.session.add(reminder)

	def get_count_pending_reminders(self, timestamp):
		log.debug("Fetching count of pending reminders")

		count = self.session.query(Reminder).filter(Reminder.target_date < timestamp).count()

		log.debug(f"Count reminders: {count}")
		return count

	def get_pending_reminders(self, count, timestamp):
		log.debug("Fetching pending reminders")

		reminders = self.session.query(Reminder)\
			.options(joinedload(Reminder.user))\
			.filter(Reminder.target_date < timestamp)\
			.limit(count)\
			.all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_all_user_reminders(self, user_name):
		log.debug(f"Fetching all reminders for u/{user_name}")

		reminders = self.session.query(Reminder)\
			.join(User)\
			.filter(User.name == user_name)\
			.order_by(Reminder.target_date.desc())\
			.all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_user_reminders(self, user_name):
		log.debug(f"Fetching reminders for u/{user_name}")

		regular_reminders = self.session.query(Reminder)\
			.join(User)\
			.filter(User.name == user_name)\
			.filter(Reminder.recurrence is None)\
			.order_by(Reminder.target_date.desc())\
			.all()

		recurring_reminders = self.session.query(Reminder)\
			.join(User)\
			.filter(User.name == user_name)\
			.filter(Reminder.recurrence is not None)\
			.order_by(Reminder.target_date.desc())\
			.all()

		log.debug(f"Found reminders: {len(regular_reminders)} : {len(recurring_reminders)}")
		return regular_reminders, recurring_reminders

	def get_reminder(self, reminder_id):
		log.debug(f"Fetching reminder by id: {reminder_id}")

		reminder = self.session.query(Reminder)\
			.options(joinedload(Reminder.user))\
			.filter_by(id=reminder_id)\
			.first()

		return reminder

	def user_has_cakeday_reminder(self, user_name):
		log.debug(f"Checking if user has cakeday reminder: {user_name}")

		reminder = self.session.query(Reminder)\
			.join(User)\
			.filter(User.name == user_name)\
			.filter(Reminder.recurrence == "one year")\
			.filter(Reminder.message == static.CAKEDAY_MESSAGE)\
			.first()

		return reminder is not None

	def delete_reminder(self, reminder):
		log.debug(f"Deleting reminder by id: {reminder.id}")
		self.session.delete(reminder)

	def delete_user_reminders(self, user_name):
		log.debug(f"Deleting all reminders for u/{user_name}")

		user_id = self.session.query(User.id).\
			filter_by(name=user_name)

		return self.session.query(Reminder).\
			filter(Reminder.user_id.in_(user_id.subquery())).\
			delete(synchronize_session=False)

	def get_all_reminders(self):
		log.debug(f"Fetching all reminders")

		reminders = self.session.query(Reminder)\
			.options(joinedload(Reminder.user))\
			.all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders
