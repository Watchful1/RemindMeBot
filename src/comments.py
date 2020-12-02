import discord_logging
import traceback

import utils
import static
import counters
from classes.reminder import Reminder
from classes.comment import DbComment
from praw_wrapper import ReturnType, PushshiftType


log = discord_logging.get_logger()


def database_set_seen(database, comment_seen):
	database.save_keystore("comment_timestamp", comment_seen.strftime("%Y-%m-%d %H:%M:%S"))


def database_get_seen(database):
	result = database.get_keystore("comment_timestamp")
	if result is None:
		log.warning("Comment time not in database, returning now")
		now = utils.datetime_now()
		database_set_seen(database, now)
		return now
	return utils.parse_datetime_string(result)


def trigger_start_of_line(body, trigger):
	for line in body.splitlines():
		if line.startswith(f"{trigger}!") or line.startswith(f"!{trigger}"):
			return True
	return False


def trigger_in_text(body, trigger):
	return f"{trigger}!" in body or f"!{trigger}" in body


def parse_comment(comment, database, count_string, reddit):
	if comment['author'] == static.ACCOUNT_NAME:
		log.debug("Comment is from remindmebot")
		return None, None
	if comment['author'] in static.BLACKLISTED_ACCOUNTS:
		log.debug("Comment is from a blacklisted account")
		return None, None

	log.info(f"{count_string}: Processing comment {comment['id']} from u/{comment['author']}")
	body = comment['body'].lower().strip()
	recurring = False
	cakeday = False
	allow_default = True
	if trigger_in_text(body, static.TRIGGER_RECURRING_LOWER):
		log.debug("Recurring reminder comment")
		recurring = True
		trigger = static.TRIGGER_RECURRING_LOWER
	elif trigger_in_text(body, static.TRIGGER_LOWER):
		log.debug("Regular comment")
		trigger = static.TRIGGER_LOWER
	elif trigger_start_of_line(body, static.TRIGGER_CAKEDAY_LOWER):
		log.debug("Cakeday comment")
		cakeday = True
		recurring = True
		trigger = static.TRIGGER_CAKEDAY_LOWER
	elif trigger_start_of_line(body, static.TRIGGER_SPLIT_LOWER):
		log.debug("Regular split comment")
		trigger = static.TRIGGER_SPLIT_LOWER
		allow_default = False
	else:
		log.debug("Command not in comment")
		return None, None

	target_date = None
	if cakeday:
		if database.user_has_cakeday_reminder(comment['author']):
			log.info("Cakeday already exists")
			return None, None

		target_date = utils.get_next_anniversary(reddit.get_user_creation_date(comment['author']))
		message_text = static.CAKEDAY_MESSAGE
		time = "1 year"

	else:
		time = utils.find_reminder_time(comment['body'], trigger)
		message_text = utils.find_reminder_message(comment['body'], trigger)

	reminder, result_message = Reminder.build_reminder(
		source=utils.reddit_link(comment['permalink']),
		message=message_text,
		user=database.get_or_add_user(comment['author']),
		requested_date=utils.datetime_from_timestamp(comment['created_utc']),
		time_string=time,
		recurring=recurring,
		target_date=target_date,
		allow_default=allow_default
	)
	if reminder is None:
		return None, None

	if cakeday:
		counters.replies.labels(source='comment', type='cake').inc()
	elif recurring:
		counters.replies.labels(source='comment', type='repeat').inc()
	elif not allow_default:
		counters.replies.labels(source='comment', type='split').inc()
	else:
		counters.replies.labels(source='comment', type='single').inc()

	database.add_reminder(reminder)

	reminder.user.recurring_sent = 0

	return reminder, result_message


def process_comment(comment, reddit, database, count_string=""):
	reminder, result_message = parse_comment(comment, database, count_string, reddit)

	if reminder is None:
		counters.replies.labels(source='comment', type='other').inc()
		log.debug("Not replying")
		return

	commented = False
	thread_id = utils.id_from_fullname(comment['link_id'])
	comment_result = None
	if database.get_comment_by_thread(thread_id) is not None:
		comment_result = ReturnType.THREAD_REPLIED
	if comment_result is None and database.get_subreddit_banned(comment['subreddit']):
		comment_result = ReturnType.FORBIDDEN
	if comment_result is None:
		reminder.thread_id = thread_id
		reddit_comment = reddit.get_comment(comment['id'])
		bldr = utils.get_footer(reminder.render_comment_confirmation(thread_id, pushshift_minutes=reddit.get_effective_pushshift_lag()))

		result_id, comment_result = reddit.reply_comment(reddit_comment, ''.join(bldr))

		if comment_result in (
				ReturnType.INVALID_USER,
				ReturnType.USER_DOESNT_EXIST,
				ReturnType.THREAD_LOCKED,
				ReturnType.DELETED_COMMENT,
				ReturnType.RATELIMIT):
			log.info(f"Unable to reply as comment: {comment_result.name}")

		elif comment_result == ReturnType.FORBIDDEN:
			log.info(f"Banned in subreddit, saving: {comment['subreddit']}")
			database.ban_subreddit(comment['subreddit'])

		else:
			if comment_result == ReturnType.NOTHING_RETURNED:
				result_id = "QUARANTINED"
				log.warning(f"Opting in to quarantined subreddit: {comment['subreddit']}")
				reddit.quarantine_opt_in(comment['subreddit'])

			if result_id is None:
				log.warning(f"Got comment ID of None when replying to {comment['id']}")
				comment_result = ReturnType.FORBIDDEN

			else:
				log.info(
					f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}, "
					f"replied as comment: {result_id}")

				if comment_result != ReturnType.QUARANTINED and comment['subreddit'] != "RemindMeBot":
					db_comment = DbComment(
						thread_id=thread_id,
						comment_id=result_id,
						reminder_id=reminder.id,
						user=reminder.user.name,
						source=reminder.source
					)
					database.save_comment(db_comment)
				commented = True

	if not commented:
		log.info(
			f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}, "
			f"replying as message: {comment_result.name}")
		bldr = utils.get_footer(reminder.render_message_confirmation(result_message, comment_result, pushshift_minutes=reddit.get_effective_pushshift_lag()))
		result = reddit.send_message(comment['author'], "RemindMeBot Confirmation", ''.join(bldr))
		if result != ReturnType.SUCCESS:
			log.info(f"Unable to send message: {result.name}")


def process_comments(reddit, database):
	comments = reddit.get_keyword_comments(static.TRIGGER_COMBINED, database_get_seen(database).replace(tzinfo=None))

	counters.pushshift_delay.labels(client="prod").set(reddit.pushshift_prod_client.lag_minutes())
	counters.pushshift_delay.labels(client="beta").set(reddit.pushshift_beta_client.lag_minutes())
	counters.pushshift_delay.labels(client="auto").set(reddit.get_effective_pushshift_lag())

	if reddit.recent_pushshift_client == PushshiftType.PROD:
		counters.pushshift_client.labels(client="prod").set(1)
		counters.pushshift_client.labels(client="beta").set(0)
	elif reddit.recent_pushshift_client == PushshiftType.BETA:
		counters.pushshift_client.labels(client="prod").set(0)
		counters.pushshift_client.labels(client="beta").set(1)
	else:
		counters.pushshift_client.labels(client="prod").set(0)
		counters.pushshift_client.labels(client="beta").set(0)

	counters.pushshift_failed.labels(client="prod").set(1 if reddit.pushshift_prod_client.failed() else 0)
	counters.pushshift_failed.labels(client="beta").set(1 if reddit.pushshift_beta_client.failed() else 0)

	counters.pushshift_seconds.labels("prod").observe(reddit.pushshift_prod_client.request_seconds)
	counters.pushshift_seconds.labels("beta").observe(reddit.pushshift_beta_client.request_seconds)

	if len(comments):
		log.debug(f"Processing {len(comments)} comments")
	i = 0
	for comment in comments[::-1]:
		i += 1
		mark_read = True
		try:
			process_comment(comment, reddit, database, f"{i}/{len(comments)}")
		except Exception as err:
			mark_read = not utils.process_error(
				f"Error processing comment: {comment['id']} : {comment['author']}",
				err, traceback.format_exc()
			)

		if mark_read:
			reddit.mark_keyword_comment_processed(comment['id'])
			database_set_seen(database, utils.datetime_from_timestamp(comment['created_utc']))
		else:
			return i

	return len(comments)


def update_comments(reddit, database):
	count_incorrect = database.get_pending_incorrect_comments()

	incorrect_items = database.get_incorrect_comments(utils.requests_available(count_incorrect))
	if len(incorrect_items):
		i = 0
		for db_comment, reminder, new_count in incorrect_items:
			i += 1
			log.info(
				f"{i}/{len(incorrect_items)}/{count_incorrect}: Updating comment : "
				f"{db_comment.comment_id} : {db_comment.current_count}/{new_count}")

			bldr = utils.get_footer(reminder.render_comment_confirmation(db_comment.thread_id, new_count))
			reddit.edit_comment(''.join(bldr), comment_id=db_comment.comment_id)
			db_comment.current_count = new_count

	else:
		log.debug("No incorrect comments")
