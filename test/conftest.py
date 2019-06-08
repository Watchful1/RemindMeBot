import sys
import pytest
import discord_logging

log = discord_logging.init_logging()

sys.path.append("src")

import database_class
import reddit_test


@pytest.fixture
def database():
	return database_class.Database(debug=True, publish=True)


@pytest.fixture
def reddit():
	return reddit_test.Reddit("Watchful1BotTest")
