from datetime import timedelta

import comments
import utils
import reddit_test
import static
from classes.reminder import Reminder
from classes.user_settings import UserSettings


def test_process_comment(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = utils.random_id()
	thread_id = utils.random_id()
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

	comments.process_comment(comment.get_pushshift_dict(), reddit, database)
	result = comment.get_first_child().body

	assert "CLICK THIS LINK" in result

	reminders = database.get_user_reminders(username)
	assert len(reminders) == 1
	assert reminders[0].user == username
	assert reminders[0].message is None
	assert reminders[0].source == utils.reddit_link(comment.permalink)
	assert reminders[0].requested_date == created
	assert reminders[0].target_date == created + timedelta(hours=24)
	assert reminders[0].db_id is not None


def test_process_comment_timezone(database, reddit):
	database.save_settings(
		UserSettings(
			user="Watchful1",
			timezone="America/Los_Angeles"
		)
	)

	username = "Watchful1"
	comment_id = utils.random_id()
	thread_id = utils.random_id()
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

	comments.process_comment(comment.get_pushshift_dict(), reddit, database)
	result = comment.get_first_child().body

	assert "Your default time zone is set to `America/Los_Angeles`" in result

	reminders = database.get_user_reminders(username)
	assert reminders[0].target_date == created + timedelta(hours=24)


def test_comment_in_thread(database, reddit):
	comment_id = utils.random_id()
	thread_id = utils.random_id()
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

	comments.process_comment(comment.get_pushshift_dict(), reddit, database)

	comment_id_2 = utils.random_id()
	comment_2 = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id_2,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id_2}/"
	)
	reddit.add_comment(comment_2)

	comments.process_comment(comment_2.get_pushshift_dict(), reddit, database)

	assert len(comment_2.children) == 0
	assert len(reddit.sent_messages) == 1
	assert reddit.sent_messages[0].author.name == static.ACCOUNT_NAME
	assert "I've already replied to another comment in this thread" in reddit.sent_messages[0].body


def test_update_incorrect_comments(database, reddit):
	comment_id1 = utils.random_id()
	thread_id1 = utils.random_id()
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
	comments.process_comment(comment1.get_pushshift_dict(), reddit, database)

	comment_id2 = utils.random_id()
	thread_id2 = utils.random_id()
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
	comments.process_comment(comment2.get_pushshift_dict(), reddit, database)

	comment_id3 = utils.random_id()
	thread_id3 = utils.random_id()
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
	comments.process_comment(comment3.get_pushshift_dict(), reddit, database)

	reminders = [
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-05 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-06 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment1.permalink),
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-07 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment2.permalink),
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-08 05:00:00")
		),
		Reminder(
			source="https://www.reddit.com/message/messages/XXXXX",
			message=utils.reddit_link(comment2.permalink),
			user="Watchful1",
			requested_date=utils.parse_datetime_string("2019-01-01 04:00:00"),
			target_date=utils.parse_datetime_string("2019-01-09 05:00:00")
		)
	]
	for reminder in reminders:
		database.save_reminder(reminder)

	comments.update_comments(reddit, database)

	assert "3 OTHERS CLICKED THIS LINK" in reddit.get_comment(comment_id1).get_first_child().body
	assert "2 OTHERS CLICKED THIS LINK" in reddit.get_comment(comment_id2).get_first_child().body
	assert "CLICK THIS LINK" in reddit.get_comment(comment_id3).get_first_child().body


def test_commenting_banned(database, reddit):
	reddit.ban_subreddit("test")

	comment_id = utils.random_id()
	thread_id = utils.random_id()
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
	comments.process_comment(comment.get_pushshift_dict(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "I'm not allowed to reply in this subreddit" in reddit.sent_messages[0].body


def test_commenting_locked(database, reddit):
	thread_id = utils.random_id()

	reddit.lock_thread(thread_id)

	comment_id = utils.random_id()
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
	comments.process_comment(comment.get_pushshift_dict(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "the thread is locked" in reddit.sent_messages[0].body


def test_commenting_deleted(database, reddit):
	comment_id = utils.random_id()
	thread_id = utils.random_id()
	comment = reddit_test.RedditObject(
		body=f"{static.TRIGGER}! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/",
		subreddit="test"
	)
	comments.process_comment(comment.get_pushshift_dict(), reddit, database)

	assert len(comment.children) == 0
	assert len(reddit.sent_messages) == 1
	assert "it was deleted before I could get to it" in reddit.sent_messages[0].body
