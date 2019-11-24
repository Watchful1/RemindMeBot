import discord_logging

from classes.user import User

log = discord_logging.get_logger()


class _DatabaseUsers:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def get_or_add_user(self, user_name, no_log=False):
		log.debug(f"Fetching user: {user_name}")
		user = self.session.query(User).filter_by(name=user_name).first()
		if user is None:
			if not no_log:
				log.info(f"Creating user: {user_name}")
			user = User(user_name)
			self.session.add(user)

		return user
