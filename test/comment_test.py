from datetime import timedelta

import comments
import utils
import reddit_test
import static


def test_process_comment(database, reddit):
	created = utils.datetime_now()
	username = "Watchful1"
	comment_id = utils.random_id()
	thread_id = utils.random_id()
	comment = reddit_test.RedditObject(
		body=f"RemindMe! 1 day",
		author=username,
		created=created,
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/"
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


def test_comment_in_thread(database, reddit):
	comment_id = utils.random_id()
	thread_id = utils.random_id()
	comment = reddit_test.RedditObject(
		body=f"RemindMe! 1 day",
		author="Watchful1",
		created=utils.datetime_now(),
		id=comment_id,
		link_id="t3_"+thread_id,
		permalink=f"/r/test/{thread_id}/_/{comment_id}/"
	)
	reddit.add_comment(comment)

	comments.process_comment(comment.get_pushshift_dict(), reddit, database)

	comment_id_2 = utils.random_id()
	comment_2 = reddit_test.RedditObject(
		body=f"RemindMe! 1 day",
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
