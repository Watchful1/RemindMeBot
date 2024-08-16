import discord_logging
from sqlalchemy.orm import joinedload

import static
from classes.stat import DbStat

log = discord_logging.get_logger()


class _DatabaseStats:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def add_increment_stat(self, subreddit, thread_id, comment_id):
		log.debug(f"Adding or incrementing new stat")
		if subreddit is None or thread_id is None:
			log.debug(f"Empty arguments, returning")
			return

		if subreddit.lower() != "askhistorians":
			log.debug(f"Subreddit doesn't match filter, returning")
			return

		existing_stat = self.session.query(DbStat)\
			.filter(DbStat.subreddit == subreddit)\
			.filter(DbStat.thread_id == thread_id)\
			.filter(DbStat.comment_id == comment_id)\
			.first()

		if existing_stat is not None:
			log.debug(f"Stat exists, incrementing")
			existing_stat.count_reminders += 1
		else:
			log.debug(f"Stat doesn't exist, creating")
			new_stat = DbStat(subreddit, thread_id, comment_id)
			self.session.add(new_stat)

	def get_stats_for_ids(self, subreddit, thread_id, comment_id=None):
		log.debug("Fetching stat")

		stat = self.session.query(DbStat)\
			.filter(DbStat.subreddit == subreddit)\
			.filter(DbStat.thread_id == thread_id)\
			.filter(DbStat.comment_id == comment_id)\
			.first()

		if stat is None:
			log.debug("No stat found")
		else:
			log.debug(f"Stat found with: {stat.count_reminders}")

		return stat

	def get_stats_for_subreddit(self, subreddit, earliest_date):
		log.debug("Fetching stats for subreddit")

		stats = self.session.query(DbStat)\
			.filter(DbStat.subreddit == subreddit)\
			.filter(DbStat.initial_date > earliest_date)\
			.order_by(DbStat.initial_date.asc())\
			.all()

		log.debug(f"{len(stats)} stats found")
		return stats

