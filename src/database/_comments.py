import sqlite3
import discord_logging

from classes.comment import DbComment
from classes.reminder import Reminder
import utils


log = discord_logging.get_logger()


def save_comment(self, db_comment):
	if not isinstance(db_comment, DbComment):
		return False

	c = self.dbConn.cursor()
	if db_comment.db_id is not None:
		log.debug(f"Updating comment: {db_comment.db_id}")
		try:
			c.execute('''
				UPDATE comments
				SET ThreadID = ?,
					CommentID = ?,
					ReminderId = ?,
					CurrentCount = ?,
					User=?,
					Source = ?
				WHERE ID = ?
			''', (
				db_comment.thread_id,
				db_comment.comment_id,
				db_comment.reminder_id,
				db_comment.current_count,
				db_comment.user,
				db_comment.source,
				db_comment.db_id))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to update reminder: {err}")
			return False
	else:
		log.debug("Saving new comment")
		try:
			c.execute('''
				INSERT INTO comments
				(ThreadID, CommentID, ReminderId, CurrentCount, User, Source)
				VALUES (?, ?, ?, ?, ?, ?)
			''', (
				db_comment.thread_id,
				db_comment.comment_id,
				db_comment.reminder_id,
				db_comment.current_count,
				db_comment.user,
				db_comment.source))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save comment: {err}")
			return False

		if c.lastrowid is not None:
			db_comment.db_id = c.lastrowid
			log.debug(f"Saved to: {db_comment.db_id}")

	self.dbConn.commit()

	return True


def get_comment_by_thread(self, thread_id):
	log.debug(f"Fetching comment for thread: {thread_id}")
	c = self.dbConn.cursor()
	c.execute('''
		SELECT ID, ThreadID, CommentID, ReminderId, CurrentCount, User, Source
		FROM comments
		WHERE ThreadID = ?
		''', (thread_id,))

	result = c.fetchone()
	if result is None or len(result) == 0:
		log.debug("No comment found")
		return None

	db_comment = DbComment(
		thread_id=result[1],
		comment_id=result[2],
		reminder_id=result[3],
		user=result[5],
		source=result[6],
		current_count=result[4],
		db_id=result[0]
	)

	return db_comment


def delete_comment(self, db_comment):
	log.debug(f"Deleting comment by id: {db_comment.db_id}")
	if db_comment.db_id is None:
		return False

	c = self.dbConn.cursor()
	c.execute('''
		DELETE FROM comments
		WHERE ID = ?
	''', (db_comment.db_id,))
	self.dbConn.commit()

	if c.rowcount == 1:
		log.debug("Comment deleted")
		return True
	else:
		log.debug("Comment not deleted")
		return False


def get_pending_incorrect_comments(self):
	log.debug("Fetching count of incorrect comments")
	c = self.dbConn.cursor()
	c.execute('''
		SELECT count(*)
		FROM comments cm
		LEFT JOIN
			(
				SELECT rm1.ID,
					   count(*) as NewCount
				FROM reminders rm1
					INNER JOIN reminders rm2
						ON rm1.Source = rm2.Message
				GROUP BY rm1.ID
			) AS rm
				ON cm.ReminderId = rm.ID
		WHERE rm.NewCount != cm.CurrentCount
		''')

	result = c.fetchone()
	if result is None or len(result) == 0:
		log.debug("No incorrect comments")
		return 0

	log.debug(f"Incorrect comments: {result[0]}")
	return result[0]


def get_incorrect_comments(self, count):
	log.debug(f"Fetching incorrect comments")
	c = self.dbConn.cursor()
	results = []
	for row in c.execute('''
		SELECT cm.ID,
			cm.ThreadID,
			cm.CommentID,
			cm.ReminderId,
			cm.CurrentCount,
			cm.User,
			cm.Source,
			rm.ID,
			rm.Source,
			rm.RequestedDate,
			rm.TargetDate,
			rm.Message,
			rm.User,
			rm.Defaulted,
			rm.NewCount
		FROM comments cm
		LEFT JOIN
			(
				SELECT rm1.ID,
					rm1.Source,
					rm1.RequestedDate,
					rm1.TargetDate,
					rm1.Message,
					rm1.User,
					rm1.Defaulted,
					count(*) as NewCount
				FROM reminders rm1
					INNER JOIN reminders rm2
						ON rm1.Source = rm2.Message
				GROUP BY rm1.ID
			) AS rm
				ON cm.ReminderId = rm.ID
		WHERE rm.NewCount != cm.CurrentCount
		LIMIT ?
		''', (count,)):
		db_comment = DbComment(
			thread_id=row[1],
			comment_id=row[2],
			reminder_id=row[3],
			user=row[5],
			source=row[6],
			current_count=row[4],
			db_id=row[0]
		)
		reminder = Reminder(
			source=row[8],
			target_date=utils.parse_datetime_string(row[10]),
			message=row[11],
			user=row[12],
			db_id=row[7],
			requested_date=utils.parse_datetime_string(row[9]),
			count_duplicates=row[14],
			thread_id=row[1],
			defaulted=row[13] == 1
		)
		results.append((db_comment, reminder))

	log.debug(f"Found incorrect comments: {len(results)}")
	return results