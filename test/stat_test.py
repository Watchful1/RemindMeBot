import utils
import static
from praw_wrapper import reddit_test
from datetime import timedelta
from classes.reminder import Reminder
import stats


def add_sample_stats(database, reddit):
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
			requested_date=utils.parse_datetime_string("2019-01-02 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshk6/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-02 04:00:00"),
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
			requested_date=utils.parse_datetime_string("2019-01-03 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message="[https://www.reddit.com/r/AskHistorians/comments/1emshj2/___/]",
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-03 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.add_reminder(reminder)

	submissions = [
		{"created": utils.parse_datetime_string("2018-01-01 04:00:00"), "id": "1emshj2", "subreddit": "AskHistorians", "title": "Title1"},
		{"created": utils.parse_datetime_string("2019-01-01 04:00:00"), "id": "1emshj8", "subreddit": "AskHistorians", "title": "Title2"},
		{"created": utils.parse_datetime_string("2019-01-01 04:00:00"), "id": "1emshk6", "subreddit": "AskHistorians", "title": "Title3"},
		{"created": utils.parse_datetime_string("2019-01-01 04:00:00"), "id": "1emshf5", "subreddit": "AskHistorians", "title": "Title4"},
	]
	for submission in submissions:
		submission_obj = reddit_test.RedditObject(
			body=f"blank",
			author="blank",
			title=submission["title"],
			created=submission["created"],
			id=submission["id"],
			permalink=f"/r/{submission['subreddit']}/comments/{submission['id']}/___/",
			subreddit=submission["subreddit"],
			prefix="t3",
		)
		reddit.add_submission(submission_obj)


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
	add_sample_stats(database, reddit)

	sub_stats = database.get_stats_for_subreddit("AskHistorians", utils.debug_time - timedelta(days=1))
	assert len(sub_stats) == 2
	assert sub_stats[0].count_reminders == 2
	assert sub_stats[1].count_reminders == 3


def test_update_dates(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	add_sample_stats(database, reddit)

	stats.update_stat_dates(reddit, database)

	count_empty_stats = len(database.get_stats_without_date())
	assert count_empty_stats == 0

	post_stat = database.get_stats_for_ids("AskHistorians", "1emshj8")
	assert post_stat.initial_date == utils.parse_datetime_string("2019-01-01 04:00:00")


def test_update_stat_wiki(database, reddit):
	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	add_sample_stats(database, reddit)

	reddit.reply_submission(
		reddit.get_submission("1emshj2"),
		"1234567890" * 30
	)
	reddit.reply_submission(
		reddit.get_submission("1emshk6"),
		"1234567890"
	)

	stats.update_stat_dates(reddit, database)
	stats.update_ask_historians(reddit, database, min_reminders=0)

	wiki_content = reddit.get_subreddit_wiki_page("SubTestBot1", "remindme")

	assert wiki_content == """Thread | Thread date | Words in top answer | Total reminders | Pending reminders
---|---|----|----|----|----
[Title2](https://www.reddit.com//r/AskHistorians/comments/1emshj8/___/)|2019-01-01 04:00:00||2|2
[Title3](https://www.reddit.com//r/AskHistorians/comments/1emshk6/___/)|2019-01-01 04:00:00||3|3
"""
