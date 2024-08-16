import utils
import notifications
import static
from praw_wrapper import reddit_test
import messages
from datetime import timedelta
from classes.reminder import Reminder


def test_add_stat(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	reminder = Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="""[https://www.reddit.com/r/AskHistorians/comments/1emshj8/___/]
RemindMe! 2 days""",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		)
	database.add_reminder(reminder)

	stat = database.get_stats_for_ids("AskHistorians", "1emshj8")
	assert stat.count_reminders == 1
	assert stat.initial_date == utils.debug_time

	reminder = Reminder(
		source="https://www.reddit.com/message/messages/YYYYY",
		message="""[https://www.reddit.com/r/AskHistorians/comments/1emshj8/___/]
RemindMe! 2 days""",
		user=database.get_or_add_user("Watchful1"),
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
	)
	database.add_reminder(reminder)

	stat = database.get_stats_for_ids("AskHistorians", "1emshj8")
	assert stat.count_reminders == 2
	assert stat.initial_date == utils.debug_time


def test_add_stats(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	reminders = [
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshj8/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshk6/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-06 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshk6/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshk6/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/history/comments/1emshf5/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-08 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshj8/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.add_reminder(reminder)

	stats = database.get_stats_for_subreddit("AskHistorians", utils.debug_time - timedelta(days=1))
	assert len(stats) == 2
	assert stats[0].count_reminders == 2
	assert stats[1].count_reminders == 3
