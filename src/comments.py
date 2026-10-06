import discord_logging
import traceback
from collections import OrderedDict
from dataclasses import dataclass

import utils
import static
import counters
from classes.reminder import Reminder
from classes.comment import DbComment
from praw_wrapper.reddit import ReturnType


log = discord_logging.get_logger()


@dataclass
class MinimalComment:
	"""The minimum set of fields parse_comment / process_comment consume. Used
	by the inbox-mention dispatch path so we don't pass raw PRAW Comments
	(whose lazy payload omits permalink and link_id) downstream.
	"""
	id: str
	author: str
	subreddit: str
	created_utc: int
	permalink: str
	link_id: str
	body: str


MENTION_MEMORY_SIZE = 500
MENTION_WARN_EVERY = 60
_processed_mentions = OrderedDict()


def reset_mention_memory():
	_processed_mentions.clear()


def record_processed_mention(comment_id):
	"""Remember a handled inbox mention id so a redelivery of it is skipped. The
	dict is bounded at MENTION_MEMORY_SIZE and evicts the oldest entry first.
	"""
	_processed_mentions[comment_id] = 0
	_processed_mentions.move_to_end(comment_id)
	while len(_processed_mentions) > MENTION_MEMORY_SIZE:
		_processed_mentions.popitem(last=False)


def duplicate_mention_reason(comment, database):
	"""Why this inbox mention should be skipped, or None if it is new.

	Reddit sometimes keeps returning the same mention as unread for hours after
	mark_read succeeds. Memory catches that within one process and returns
	("memory", repeat_count); the database check catches a redelivery after a
	restart and returns ("database", 0). A reminder saved before a transient
	reply failure also counts as a database hit, so that redelivery loses its
	confirmation. Accepted, see the spec.
	"""
	if comment.id in _processed_mentions:
		_processed_mentions[comment.id] += 1
		_processed_mentions.move_to_end(comment.id)
		return "memory", _processed_mentions[comment.id]

	source = utils.reddit_link(comment.permalink)
	if database.get_reminder_by_user_source(comment.author, source) is not None:
		return "database", 0

	return None


def should_warn_duplicate(reason, count):
	"""Whether a skipped duplicate should be logged as a warning.

	Memory hits warn on the first repeat and then every MENTION_WARN_EVERY, so a
	multi-hour incident sends Discord a line about every 30 minutes instead of
	one per loop. Database hits happen once per restart and always warn.
	"""
	if reason == "database":
		return True
	return count == 1 or count % MENTION_WARN_EVERY == 0


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


def body_contains_command(body):
	lower = body.lower().strip()
	return (
		trigger_in_text(lower, static.TRIGGER_RECURRING_LOWER)
		or trigger_in_text(lower, static.TRIGGER_LOWER)
		or trigger_start_of_line(lower, static.TRIGGER_CAKEDAY_LOWER)
		or trigger_start_of_line(lower, static.TRIGGER_SPLIT_LOWER)
	)


def is_pure_mention(body):
	"""True if the body is a username mention with no bang-command.

	These are handled by the inbox dispatch path in messages.py and should be
	skipped by the ingest pipeline to avoid duplicate reminders.
	"""
	if static.MENTION_PATTERN.search(body.lower().strip()) is None:
		return False
	return not body_contains_command(body)


def parse_comment(comment, database, count_string, reddit):
	if comment.author == static.ACCOUNT_NAME:
		log.debug("Comment is from remindmebot")
		return None, None, False
	if comment.author in static.BLACKLISTED_ACCOUNTS:
		log.debug("Comment is from a blacklisted account")
		return None, None, False

	log.info(f"{count_string}: Processing comment {comment.id} from u/{comment.author}")
	body = comment.body.lower().strip()
	recurring = False
	cakeday = False
	mention = False
	allow_default = True
	mention_match = static.MENTION_PATTERN.search(body)
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
	elif mention_match is not None:
		keyword = mention_match.group(1)
		mention = True
		trigger = mention_match.group(0)
		if keyword == "repeat":
			log.debug("Mention recurring reminder")
			recurring = True
		elif keyword == "cakeday":
			log.debug("Mention cakeday")
			cakeday = True
			recurring = True
		else:
			log.debug("Mention single reminder")
	else:
		log.debug("Command not in comment")
		return None, None, False

	target_date = None
	if cakeday:
		if database.user_has_cakeday_reminder(comment.author):
			log.info("Cakeday already exists")
			return None, None, False

		target_date = utils.get_next_anniversary(reddit.get_user_creation_date(comment.author))
		message_text = static.CAKEDAY_MESSAGE
		time = "1 year"

	else:
		time = utils.find_reminder_time(comment.body, trigger)
		if time is None and mention:
			time = utils.find_reminder_time_next_line(comment.body, trigger)
		message_text = utils.find_reminder_message(comment.body, trigger)

	reminder, result_message = Reminder.build_reminder(
		source=utils.reddit_link(comment.permalink),
		message=message_text,
		user=database.get_or_add_user(comment.author),
		requested_date=utils.datetime_from_timestamp(comment.created_utc),
		time_string=time,
		recurring=recurring,
		target_date=target_date,
		allow_default=allow_default
	)
	if reminder is None:
		return None, None, False

	trigger_label = 'mention' if mention else 'command'
	if cakeday:
		counters.replies.labels(source='comment', type='cake', trigger=trigger_label).inc()
	elif recurring:
		counters.replies.labels(source='comment', type='repeat', trigger=trigger_label).inc()
	elif not allow_default:
		counters.replies.labels(source='comment', type='split', trigger=trigger_label).inc()
	else:
		counters.replies.labels(source='comment', type='single', trigger=trigger_label).inc()

	database.add_reminder(reminder)

	reminder.user.recurring_sent = 0

	return reminder, result_message, mention


def process_comment(comment, reddit, database, count_string=""):
	reminder, result_message, from_mention = parse_comment(comment, database, count_string, reddit)

	if reminder is None:
		counters.replies.labels(source='comment', type='other', trigger='command').inc()
		log.debug("Not replying")
		return

	commented = False
	thread_id = utils.id_from_fullname(comment.link_id)
	comment_result = None
	if database.get_comment_by_thread(thread_id) is not None:
		comment_result = ReturnType.THREAD_REPLIED
	if comment_result is None and database.get_subreddit_banned(comment.subreddit):
		comment_result = ReturnType.FORBIDDEN
	comment_age_seconds = (utils.datetime_now() - utils.datetime_from_timestamp(comment.created_utc)).total_seconds()
	if comment_result is None:
		reminder.thread_id = thread_id
		reddit_comment = reddit.get_comment(comment.id)
		bldr = utils.get_footer(reminder.render_comment_confirmation(thread_id, comment_age_seconds=comment_age_seconds, suppress_mention_nudge=from_mention))

		result_id, comment_result = reddit.reply_comment(reddit_comment, ''.join(bldr))

		if comment_result in (
				ReturnType.INVALID_USER,
				ReturnType.USER_DOESNT_EXIST,
				ReturnType.THREAD_LOCKED,
				ReturnType.DELETED_COMMENT,
				ReturnType.RATELIMIT,
				ReturnType.COMMENT_UNREPLIABLE):
			log.info(f"Unable to reply as comment: {comment_result.name}")

		elif comment_result in (
				ReturnType.FORBIDDEN,
				ReturnType.SUBREDDIT_OUTBOUND_LINKING_DISALLOWED,
				ReturnType.COMMENT_GUIDANCE_VALIDATION_FAILED,):
			log.info(f"Banned in subreddit, saving: {comment.subreddit}")
			database.ban_subreddit(comment.subreddit)

		elif result_id is None:
			log.info(f"Reply failed, no returned comment id")

		else:
			if comment_result == ReturnType.NOTHING_RETURNED:
				result_id = "QUARANTINED"
				log.warning(f"Opting in to quarantined subreddit: {comment.subreddit}")
				reddit.quarantine_opt_in(comment.subreddit)

			log.info(
				f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}, "
				f"replied as comment: {result_id}")

			if comment_result != ReturnType.QUARANTINED and comment.subreddit != "RemindMeBot":
				db_comment = DbComment(
					thread_id=thread_id,
					comment_id=result_id,
					reminder_id=reminder.id,
					user=reminder.user.name,
					source=reminder.source,
					from_mention=from_mention
				)
				database.save_comment(db_comment)
			commented = True

	if not commented:
		log.info(
			f"Reminder created: {reminder.id} : {utils.get_datetime_string(reminder.target_date)}, "
			f"replying as message: {comment_result.name}")
		bldr = utils.get_footer(reminder.render_message_confirmation(result_message, comment_result, comment_age_seconds=comment_age_seconds, suppress_mention_nudge=from_mention))
		result = reddit.send_message(comment.author, "RemindMeBot Confirmation", ''.join(bldr), retry_seconds=600)
		if result != ReturnType.SUCCESS:
			log.info(f"Unable to send message: {result.name}")


def process_comments(reddit, database, ingest_database):
	if ingest_database is None:
		log.debug("No ingest database passed, skipping comment search")
		return 0
	comments = ingest_database.get_comments(limit=30)

	if len(comments):
		log.debug(f"Processing {len(comments)} comments")
	i = 0
	for comment in comments[::-1]:
		i += 1
		mark_read = True
		if is_pure_mention(comment.body):
			log.debug(f"Skipping pure mention from ingest, owned by inbox dispatch: {comment.id}")
		else:
			try:
				process_comment(comment, reddit, database, f"{i}/{len(comments)}")
			except Exception as err:
				mark_read = not utils.process_error(
					f"Error processing comment: {comment.id} : {comment.author}",
					err, traceback.format_exc()
				)

		if mark_read:
			ingest_database.delete_comment(comment)
			ingest_database.commit()
			database_set_seen(database, utils.datetime_from_timestamp(comment.created_utc))
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

			bldr = utils.get_footer(reminder.render_comment_confirmation(db_comment.thread_id, new_count, suppress_mention_nudge=db_comment.from_mention))
			try:
				result = reddit.edit_comment(''.join(bldr), comment_id=db_comment.comment_id)
				if result != ReturnType.SUCCESS:
					log.warning(f"Failed to edit comment {db_comment.comment_id}: {result}")
			except Exception as err:
				utils.process_error(f"Error updating comment: {db_comment.comment_id}", err, traceback.format_exc())
				continue

			db_comment.current_count = new_count

	else:
		log.debug("No incorrect comments")
