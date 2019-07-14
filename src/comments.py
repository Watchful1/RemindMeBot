import discord_logging
import traceback

import utils
import static
from classes.reminder import Reminder
from classes.comment import DbComment
from classes.enums import ReturnType


log = discord_logging.get_logger()


def database_set_seen(database, comment_seen):
	database.save_keystore("remindme_comment", comment_seen.strftime("%Y-%m-%d %H:%M:%S"))


def database_get_seen(database):
	result = database.get_keystore("remindme_comment")
	if result is None:
		log.warning("Comment time not in database, returning now")
		return utils.datetime_now()
	return utils.parse_datetime_string(result)


def parse_comment(comment, database, count_string):
	if comment['author'] == static.ACCOUNT_NAME:
		log.debug("Comment is from remindmebot")
		return None

	log.info(f"{count_string}: Processing comment {comment['id']} from u/{comment['author']}")
	body = comment['body'].lower()
	if f"{static.TRIGGER_LOWER}!" not in body and f"!{static.TRIGGER_LOWER}" not in body:
		log.debug("Command not in comment")
		return None

	time = utils.find_reminder_time(comment['body'])

	message_text = utils.find_reminder_message(comment['body'])

	timezone = database.get_settings(comment['author']).timezone

	reminder = Reminder(
		source=utils.reddit_link(comment['permalink']),
		message=message_text,
		user=comment['author'],
		requested_date=utils.datetime_from_timestamp(comment['created_utc']),
		time_string=time,
		timezone=timezone
	)
	if not reminder.valid:
		return None

	if not database.save_reminder(reminder):
		reminder.result_message = "Something went wrong saving the reminder"
		reminder.valid = False
		log.warning(reminder.result_message)

	return reminder


def process_comment(comment, reddit, database, count_string=""):
	reminder = parse_comment(comment, database, count_string)

	if reminder is None or not reminder.valid:
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
		bldr = utils.get_footer(reminder.render_comment_confirmation())

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
			if comment_result == ReturnType.QUARANTINED:
				result_id = "QUARANTINED"
				log.warning(f"Opting in to quarantined subreddit: {comment['subreddit']}")
				reddit.quarantine_opt_in(comment['subreddit'])

			log.info(
				f"Reminder created: {reminder.db_id} : {utils.get_datetime_string(reminder.target_date)}, "
				f"replied as comment: {result_id}")

			database.save_reminder(reminder)

			if comment_result != ReturnType.QUARANTINED:
				db_comment = DbComment(
					thread_id=thread_id,
					comment_id=result_id,
					reminder_id=reminder.db_id,
					user=reminder.user,
					source=reminder.source
				)
				database.save_comment(db_comment)
			commented = True

	if not commented:
		log.info(
			f"Reminder created: {reminder.db_id} : {utils.get_datetime_string(reminder.target_date)}, "
			f"replying as message: {comment_result.name}")
		bldr = utils.get_footer(reminder.render_message_confirmation(comment_result))
		result = reddit.send_message(comment['author'], "RemindMeBot Confirmation", ''.join(bldr))
		if result != ReturnType.SUCCESS:
			log.info(f"Unable to send message: {result.name}")


def process_comments(reddit, database):
	comments = reddit.get_keyword_comments(static.TRIGGER_LOWER, database_get_seen(database))
	if len(comments):
		log.debug(f"Processing {len(comments)} comments")
	i = 0
	for comment in comments[::-1]:
		i += 1
		try:
			process_comment(comment, reddit, database, f"{i}/{len(comments)}")
		except Exception:
			log.warning(f"Error processing comment: {comment['id']} : {comment['author']}")
			log.warning(traceback.format_exc())

		reddit.mark_keyword_comment_processed(comment['id'])
		database_set_seen(database, utils.datetime_from_timestamp(comment['created_utc']))

	return len(comments)


def update_comments(reddit, database):
	count_incorrect = database.get_pending_incorrect_comments()

	incorrect_items = database.get_incorrect_comments(utils.requests_available(count_incorrect))
	if len(incorrect_items):
		i = 0
		for db_comment, reminder in incorrect_items:
			i += 1
			log.info(
				f"{i}/{len(incorrect_items)}/{count_incorrect}: Updating comment : "
				f"{db_comment.comment_id} : {db_comment.current_count}/{reminder.count_duplicates}")

			bldr = utils.get_footer(reminder.render_comment_confirmation())
			reddit.edit_comment(''.join(bldr), comment_id=db_comment.comment_id)
			db_comment.current_count = reminder.count_duplicates
			database.save_comment(db_comment)

	else:
		log.debug("No incorrect comments")
