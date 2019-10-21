import discord_logging
from datetime import timedelta

import utils
from classes.subreddit import Subreddit

log = discord_logging.get_logger()


class _DatabaseSubreddit:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def ban_subreddit(self, subreddit):
		log.debug(f"Banning subreddit: {subreddit}")
		self.session.merge(Subreddit(subreddit, True))

	def get_subreddit_banned(self, subreddit):
		log.debug(f"Getting subreddit ban: {subreddit}")
		days_ago = utils.datetime_now() - timedelta(days=30)
		return self.session.query(Subreddit)\
			.filter_by(subreddit=subreddit)\
			.filter_by(banned=True)\
			.filter(Subreddit.ban_checked < days_ago)\
			.scalar()