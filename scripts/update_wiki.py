import discord_logging
import traceback
from datetime import timedelta
import praw_wrapper

log = discord_logging.init_logging()

import utils
from database import Database
import stats


if __name__ == "__main__":
	reddit = praw_wrapper.Reddit("Watchful1")
	database = Database()

	stats.update_stats(reddit, database)
