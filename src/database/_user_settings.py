import discord_logging
from classes.user_settings import UserSettings


log = discord_logging.get_logger()


class _DatabaseUserSettings:
	def __init__(self):
		self.dbConn = self.dbConn  # for pycharm linting

	def save_settings(self, user_settings):
		log.debug(f"Saving settings: {user_settings.user}")
		c = self.dbConn.cursor()
		c.execute('''
			REPLACE INTO user_settings
			(User, TimeZone)
			VALUES (?, ?)
		''', (user_settings.user, user_settings.timezone))
		self.dbConn.commit()

		return True

	def get_settings(self, user):
		log.debug(f"Fetching settings: {user}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT TimeZone
			FROM user_settings
			WHERE User = ?
			''', (user,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("User not found")
			user_settings = UserSettings(
				user=user
			)

		else:
			log.debug(f"User found")
			user_settings = UserSettings(
				user=user,
				timezone=result[0]
			)

		return user_settings
