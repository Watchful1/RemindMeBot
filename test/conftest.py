import sys
import pytest

sys.path.append("src")

import main
import database_class
import reddit_class


@pytest.fixture
def remind_me_bot():
	return main.RemindMeBot()


@pytest.fixture
def database():
	return database_class.Database(debug=True)


@pytest.fixture
def reddit():
	return reddit_class.Reddit("Watchful1BotTest", False, True)
