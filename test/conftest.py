import sys
import pytest
import discord_logging

log = discord_logging.init_logging(debug=True)

sys.path.append("src")

import static
from database import Database
from praw_wrapper import reddit_test


@pytest.fixture
def database():
	return Database(debug=True, publish=True)


@pytest.fixture
def reddit():
	reddit = reddit_test.Reddit("Watchful1BotTest")
	static.ACCOUNT_NAME = reddit.username
	return reddit
