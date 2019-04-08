import sys
import pytest

sys.path.append("src")

import main
import database_class
import reddit_test


@pytest.fixture
def remind_me_bot():
	return main.RemindMeBot()


@pytest.fixture
def database():
	return database_class.Database(debug=True)


@pytest.fixture
def reddit():
	return reddit_test.Reddit("Watchful1BotTest")
