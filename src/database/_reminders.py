import discord_logging

from classes.reminder import Reminder
from classes.user_settings import UserSettings

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

		reminders = self.session.query(Reminder).filter(Reminder.target_date < timestamp).limit(count).all()
		self.add_user_settings_to_reminders(reminders)

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_user_reminders(self, user):
		log.debug(f"Fetching reminders for u/{user}")

		reminders = self.session.query(Reminder).filter_by(user=user).all()
		self.add_user_settings_to_reminders(reminders)

		log.debug(f"Found reminders: {len(reminders)}")
		return reminders

	def get_reminder(self, reminder_id):
		log.debug(f"Fetching reminder by id: {reminder_id}")

		reminder = self.session.query(Reminder).filter_by(id=reminder_id).first()
		self.add_user_setting_to_reminder(reminder)

		return reminder

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

	def add_user_settings_to_reminders(self, reminders):
		user_settings_list = self.session.query(UserSettings).filter(UserSettings.user.in_([r.user for r in reminders])).all()
		user_settings_dict = {s.user: s for s in user_settings_list}
		for reminder in reminders:
			if reminder.user in user_settings_dict:
				reminder.user_settings = user_settings_dict[reminder.user]
			else:
				reminder.user_settings = UserSettings(reminder.user)

	def add_user_setting_to_reminder(self, reminder):
		user_setting = self.session.query(UserSettings).filter(UserSettings.user == reminder.user).first()
		if user_setting is None:
			reminder.user_settings = UserSettings(reminder.user)
		else:
			reminder.user_settings = user_setting
