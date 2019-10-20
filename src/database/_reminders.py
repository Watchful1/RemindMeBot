import discord_logging

from classes.reminder import Reminder

log = discord_logging.get_logger()


class _DatabaseReminders:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def save_reminder(self, reminder):
		if reminder.id is None:
			log.debug("Saving new reminder")
		else:
			log.debug(f"Updating reminder: {reminder.id}")
		try:
			self.session.merge(reminder)
		except:
			return False
		return True

	def get_count_pending_reminders(self, timestamp):
		log.debug("Fetching count of pending reminders")

		count = self.session.query(Reminder).filter(Reminder.target_date < timestamp).count()

		log.debug(f"Count reminders: {count}")
		return count

	def get_pending_reminders(self, count, timestamp):
		log.debug("Fetching pending reminders")

		reminders = self.session.query(Reminder).filter(Reminder.target_date < timestamp)[:count + 1].all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_user_reminders(self, user):
		log.debug(f"Fetching reminders for u/{user}")

		reminders = self.session.query(Reminder).filter_by(user=user).all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_reminder(self, reminder_id):
		log.debug(f"Fetching reminder by id: {reminder_id}")

		return self.session.query(Reminder).filter_by(id=reminder_id).first()

	def delete_reminder(self, reminder):
		log.debug(f"Deleting reminder by id: {reminder.id}")
		self.session.delete(reminder)

	def delete_user_reminders(self, user):
		log.debug(f"Deleting all reminders for u/{user}")

		return self.session.query(Reminder).filter_by(user=user).delete()

	def get_all_reminders(self):
		log.debug(f"Fetching all reminders")

		reminders = self.session.query(Reminder).all()

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders
