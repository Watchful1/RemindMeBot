from datetime import timedelta

import comments
import utils
from praw_wrapper import reddit_test, IngestDatabase, IngestComment
import static
from classes.reminder import Reminder


def test_process_comments_ingest(database, reddit):
	ingest_database = IngestDatabase(debug=True)
	ingest_database.set_default_client("updateme")

	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	ingest_database.add_comment(
		IngestComment(
			id=comment.id,
			author=comment.author.name,
			subreddit=comment.subreddit.display_name,
			created_utc=comment.created_utc,
			permalink=comment.permalink,
			link_id=comment.link_id,
			body=comment.body,
			client_id=ingest_database.default_client_id,
		)
	)

	comments.process_comments(reddit, database, ingest_database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None
	assert reminders[0].recurrence is None

	assert ingest_database.get_count_comments(None) == 0


def test_process_comments_skips_pure_mention(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	ingest_database = IngestDatabase(debug=True)
	ingest_database.set_default_client("updateme")

	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	ingest_database.add_comment(
		IngestComment(
			id=comment.id,
			author=comment.author.name,
			subreddit=comment.subreddit.display_name,
			created_utc=comment.created_utc,
			permalink=comment.permalink,
			link_id=comment.link_id,
			body=comment.body,
			client_id=ingest_database.default_client_id,
		)
	)

	comments.process_comments(reddit, database, ingest_database)

	# ingest entry should be marked-read (deleted) so it doesn't reappear
	assert ingest_database.get_count_comments(None) == 0
	# no reminder created via ingest — the inbox dispatch is supposed to own this
	assert len(database.get_all_user_reminders(username)) == 0
	# no reply posted on the comment
	assert len(comment.children) == 0


def test_process_comment(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None
	assert reminders[0].recurrence is None


def test_process_comment_split(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_SPLIT}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None
	assert reminders[0].recurrence is None


def test_process_comment_split_no_date(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_SPLIT}! test",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	assert len(comment.children) == 0

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 0


def test_process_comment_split_not_start(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"this is a test {static.TRIGGER_SPLIT}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	assert len(comment.children) == 0

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 0


def test_process_comment_timezone(database, reddit):
	user = database.get_or_add_user(user_name="Watchful1")
	user.timezone = "America/Los_Angeles"

	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	created = utils.datetime_now()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "default time zone" in result
	assert "`America/Los_Angeles`" in result

	reminders = database.get_all_user_reminders(username)
	assert reminders[0].target_date == created + timedelta(hours=24)


def test_comment_in_thread(database, reddit):
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	comment_id_2 = reddit_test.random_id()
	comment_2 = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id_2,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id_2}/",
		subreddit="test"
	)
	reddit.add_comment(comment_2)

	comments.process_comment(comment_2.get_ingest_comment(), reddit, database)

	assert len(comment_2.children) == 0
	assert len(reddit.sent_messages) == 1
	assert reddit.sent_messages[0].author.name == static.ACCOUNT_NAME
	assert "I've already replied to another comment in this thread" in reddit.sent_messages[0].body


def test_update_incorrect_comments(database, reddit):
	comment_id1 = reddit_test.random_id()
	thread_id1 = reddit_test.random_id()
	comment1 = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id1,
		link_id="t3_"+thread_id1,
		permalink=f"/r/test/{thread_id1}/_/{comment_id1}/",
		subreddit="test"
	)
	reddit.add_comment(comment1)
	comments.process_comment(comment1.get_ingest_comment(), reddit, database)

	comment_id2 = reddit_test.random_id()
	thread_id2 = reddit_test.random_id()
	comment2 = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id2,
		link_id="t3_"+thread_id2,
		permalink=f"/r/test/{thread_id2}/_/{comment_id2}/",
		subreddit="test"
	)
	reddit.add_comment(comment2)
	comments.process_comment(comment2.get_ingest_comment(), reddit, database)

	comment_id3 = reddit_test.random_id()
	thread_id3 = reddit_test.random_id()
	comment3 = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id3,
		link_id="t3_"+thread_id3,
		permalink=f"/r/test/{thread_id3}/_/{comment_id3}/",
		subreddit="test"
	)
	reddit.add_comment(comment3)
	comments.process_comment(comment3.get_ingest_comment(), reddit, database)

	reminders = [
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-06 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment2.permalink),
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-08 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment2.permalink),
			user=database.get_or_add_user("Watchful1"),
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.add_reminder(reminder)

	comments.update_comments(reddit, database)

	assert "3 OTHERS CLICKED THIS LINK" in reddit.get_comment(comment_id1).get_first_child().body
	assert "2 OTHERS CLICKED THIS LINK" in reddit.get_comment(comment_id2).get_first_child().body
	assert "CLICK THIS LINK" in reddit.get_comment(comment_id3).get_first_child().body


def test_commenting_banned(database, reddit):
	reddit.ban_subreddit("test")

	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit=reddit.subreddits["test"]
	)
	reddit.add_comment(comment)
	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "I'm not allowed to reply in this subreddit" in reddit.sent_messages[0].body


def test_commenting_locked(database, reddit):
	thread_id = reddit_test.random_id()

	reddit.lock_thread(thread_id)

	comment_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(comment)
	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "the thread is locked" in reddit.sent_messages[0].body


def test_commenting_deleted(database, reddit):
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "it was deleted before I could get to it" in reddit.sent_messages[0].body


def test_process_recurring_comment_period(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_RECURRING}! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result
	assert "and then every" in result
	assert "`1 day`" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None
	assert reminders[0].recurrence == "1 day"


def test_process_recurring_comment_time(database, reddit):
	created = utils.parse_datetime_string("2019-01-05 12:00:00")
	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_RECURRING}! 9 pm",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result
	assert "and then every" in result
	assert "9 hours" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=9)
	assert reminders[0].id is not None
	assert reminders[0].recurrence == "9 pm"


def test_fail_recurring_comment(database, reddit):
	created = utils.parse_datetime_string("2019-01-04 12:00:00")
	utils.debug_time = utils.parse_datetime_string("2019-01-04 12:00:00")
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_RECURRING}! 2019-01-05",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	assert len(comment.children) == 0


def test_process_cakeday_comment(database, reddit):
	username = "Watchful1"
	user = reddit_test.User(username, utils.parse_datetime_string("2015-05-05 15:25:17").timestamp())
	reddit.add_user(user)
	created = utils.parse_datetime_string("2019-01-05 11:00:00")
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER_CAKEDAY}!",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "to remind you of your cakeday" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == utils.parse_datetime_string("2019-05-05 15:25:17")
	assert reminders[0].id is not None
	assert reminders[0].recurrence == "1 year"
	assert reminders[0].message == "Happy Cakeday!"


def test_process_mention_single(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user.name == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].id is not None
	assert reminders[0].recurrence is None


def test_process_mention_single_slash_form(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"/u/{static.ACCOUNT_NAME} 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].recurrence is None


def test_process_mention_repeat(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} repeat 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result
	assert "and then every" in result
	assert "`1 day`" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].recurrence == "1 day"


def test_process_mention_cakeday(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	username = "Watchful1"
	user = reddit_test.User(username, utils.parse_datetime_string("2015-05-05 15:25:17").timestamp())
	reddit.add_user(user)
	created = utils.parse_datetime_string("2019-01-05 11:00:00")
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} cakeday",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	utils.debug_time = utils.parse_datetime_string("2019-01-05 12:00:00")
	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	result = comment.get_first_child().body

	assert "to remind you of your cakeday" in result

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].target_date == utils.parse_datetime_string("2019-05-05 15:25:17")
	assert reminders[0].recurrence == "1 year"
	assert reminders[0].message == "Happy Cakeday!"


def test_process_mention_case_insensitive(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"U/{static.ACCOUNT_NAME.upper()} 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].target_date == created + timedelta(hours=24)


def test_process_mention_disabled(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", False)
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		author=username,
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)
	assert len(comment.children) == 0

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 0


def test_process_mention_no_time_defaults(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME}",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)

	reddit.add_comment(comment)

	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].target_date == created + timedelta(hours=24)


class _LazyMentionComment:
	"""Mimics a PRAW inbox Comment whose lazy payload omits permalink.

	Reddit's inbox JSON includes subreddit, author, body, link_id, etc. — those
	are set directly. permalink is the one attribute PRAW lazy-fetches, and
	the fetch is failing in production.
	"""
	def __init__(self, comment_id, author, body, link_id, subreddit, created):
		self.id = comment_id
		self.author = author
		self.body = body
		self.link_id = link_id
		self.subreddit = subreddit
		self.created_utc = created.timestamp()

	def __getattr__(self, name):
		raise AttributeError(f"'_LazyMentionComment' object has no attribute '{name}'")


def test_process_mention_with_lazy_praw_comment(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)

	username = "Watchful1"
	created = utils.datetime_now()
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()

	# Register a normal comment so reddit.get_comment / reply_comment have something
	# to operate on during the reply step (production hits this path via PRAW too).
	registered = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(registered)

	# Dispatch with the lazy stand-in — what production actually hands process_comment.
	lazy = _LazyMentionComment(
		comment_id=comment_id,
		author=username,
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		link_id="t3_"+thread_id,
		subreddit="test",
		created=created,
	)
	comments.process_comment(lazy, reddit, database)

	reminders = database.get_all_user_reminders(username)
	assert len(reminders) == 1
	# Source URL fell back to the constructed /comments/{post}/_/{comment}/ form.
	assert reminders[0].source == utils.reddit_link(f"/comments/{thread_id}/_/{comment_id}/")
	# Reply still posted despite the lazy attributes.
	assert "CLICK THIS LINK" in registered.get_first_child().body


def _make_dup_reminder(database, permalink, target_date):
	return Reminder(
		source="https://www.reddit.com/message/messages/XXXXX",
		message=utils.reddit_link(permalink),
		user=database.get_or_add_user("Watchful1"),
		requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
		target_date=utils.parse_datetime_string(target_date)
	)


def test_update_comments_suppresses_nudge_for_mention(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "MENTION_REMINDERS_ENABLED", True)
	monkeypatch.setattr(static, "ENCOURAGE_MENTIONS_IN_REPLY", True)
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"u/{static.ACCOUNT_NAME} 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(comment)
	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	# first reply should already suppress the nudge
	first_body = comment.get_first_child().body
	assert "is switching to username summons" not in first_body

	# inflate the duplicate count and re-render
	for target in ("2019-01-05 05:00:00", "2019-01-06 05:00:00"):
		database.add_reminder(_make_dup_reminder(database, comment.permalink, target))
	comments.update_comments(reddit, database)

	edited_body = comment.get_first_child().body
	assert "2 OTHERS CLICKED THIS LINK" in edited_body
	assert "is switching to username summons" not in edited_body


def test_update_comments_shows_nudge_for_command(database, reddit, monkeypatch):
	monkeypatch.setattr(static, "ENCOURAGE_MENTIONS_IN_REPLY", True)
	comment_id = reddit_test.random_id()
	thread_id = reddit_test.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	reddit.add_comment(comment)
	comments.process_comment(comment.get_ingest_comment(), reddit, database)

	first_body = comment.get_first_child().body
	assert "is switching to username summons" in first_body

	for target in ("2019-01-05 05:00:00", "2019-01-06 05:00:00"):
		database.add_reminder(_make_dup_reminder(database, comment.permalink, target))
	comments.update_comments(reddit, database)

	edited_body = comment.get_first_child().body
	assert "2 OTHERS CLICKED THIS LINK" in edited_body
	assert "is switching to username summons" in edited_body
