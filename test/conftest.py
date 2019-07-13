import sys
import pytest
import discord_logging

log = discord_logging.init_logging(debug=True)

sys.path.append("src")

from database import Database
import reddit_test


@pytest.fixture
def database():
	return Database(debug=True, publish=True)


@pytest.fixture
def reddit():
	return reddit_test.Reddit("Watchful1BotTest")
