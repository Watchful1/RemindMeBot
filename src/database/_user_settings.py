import discord_logging

from classes.user_settings import UserSettings

log = discord_logging.get_logger()


class _DatabaseUserSettings:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def save_settings(self, user_settings):
		log.debug(f"Saving settings: {user_settings.user}")
		self.session.merge(user_settings)

	def get_settings(self, user):
		log.debug(f"Fetching settings: {user}")
		user_settings = self.session.query(UserSettings).filter_by(user=user).first()

		if user_settings is None:
			user_settings = UserSettings(user)

		return user_settings
