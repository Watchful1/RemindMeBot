import pytest
import sys
from datetime import datetime

sys.path.append("src")

import main
import database_class
import messages


@pytest.fixture
def remind_me_bot():
	return main.RemindMeBot()


@pytest.fixture
def database():
	return database_class.Database(True)


def test_add_reminder(database):
	class TempMessage:
		pass
	message = TempMessage()
	message.body = "[reminder]\n1 day"
	message.id = "testid"
	message.fullname = "t3_testid"
	message.author = TempMessage()
	message.author.name = "Watchful1"
	message.created_utc = datetime.utcnow().timestamp()

	result = messages.process_remind_me(message, database)
	print(result)
