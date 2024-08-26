import discord_logging
from datetime import timedelta
import time

log = discord_logging.get_logger()

import utils


def update_stat_dates(reddit, database):
	empty_stats = database.get_stats_without_date()
	if empty_stats:
		full_names = {}
		for stat in empty_stats:
			if stat.comment_id is not None:
				full_names[f"t1_{stat.comment_id}"] = stat
			else:
				full_names[f"t3_{stat.thread_id}"] = stat

		reddit_objects = reddit.call_info(full_names.keys())
		count_updated = 0
		for reddit_object in reddit_objects:
			stat = full_names[reddit_object.name]
			stat.initial_date = utils.datetime_from_timestamp(reddit_object.created_utc)
			count_updated += 1

		if count_updated != 0:
			log.info(f"Updated {count_updated} stats")
		if count_updated != len(empty_stats):
			for stat in empty_stats:
				if stat.initial_date is None:
					log.warning(f"Unable to retrieve date for stat: {stat}")


def update_ask_historians(reddit, database, min_reminders=10, days_back=7):
	startTime = time.perf_counter()
	earliest_date = utils.datetime_now() - timedelta(days=days_back)
	stats = database.get_stats_for_subreddit("AskHistorians", earliest_date, min_reminders=min_reminders, thread_only=True)

	bldr = utils.str_bldr()
	bldr.append("Thread | Thread date | Words in top answer | Total reminders | Pending reminders\n")
	bldr.append("---|---|----|----|----|----\n")

	for stat in stats:
		reddit_submission = reddit.get_submission(stat.thread_id)
		bldr.append(f"[{utils.truncate_string(reddit_submission.title, 60)}](https://www.reddit.com/{reddit_submission.permalink})|")
		bldr.append(f"{utils.get_datetime_string(utils.datetime_from_timestamp(reddit_submission.created_utc), '%Y-%m-%d %H:%M %Z')}|")

		top_comment = None
		for comment in reddit_submission.comments:
			if comment.author is not None and comment.author.name != "AutoModerator" and comment.distinguished is None:
				top_comment = comment
				break
		#utils.datetime_from_timestamp(comment.created_utc)
		if top_comment is None:
			bldr.append(f"|")
		else:
			bldr.append(f"{utils.surround_int_over_threshold(len(top_comment.body.split(' ')), '**', 350)}|")

		bldr.append(f"{utils.surround_int_over_threshold(stat.count_reminders, '**', 50)}|")
		bldr.append(f"{utils.surround_int_over_threshold(database.get_reminders_with_keyword(stat.thread_id, earliest_date), '**', 50)}")
		bldr.append(f"\n")

	old_wiki_content = reddit.get_subreddit_wiki_page("AskHistorians", "remindme")
	new_wiki_content = ''.join(bldr)
	log.debug(new_wiki_content)
	if old_wiki_content == new_wiki_content:
		log.debug("Wiki content unchanged")
	else:
		log.info(f"Updated stats wiki in: {int(time.perf_counter() - startTime)}")
		reddit.update_subreddit_wiki_page("AskHistorians", "remindme", new_wiki_content)


def update_stats(reddit, database):
	update_stat_dates(reddit, database)

	update_ask_historians(reddit, database)





