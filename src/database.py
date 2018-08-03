import sqlite3
from datetime import datetime

from reminder import Reminder
import globals

dbConn = None


def init():
	global dbConn

	dbConn = sqlite3.connect(globals.DATABASE_NAME)
	c = dbConn.cursor()
	c.execute('''
		CREATE TABLE IF NOT EXISTS reminders (
			ID INTEGER PRIMARY KEY AUTOINCREMENT,
			SourceID VARCHAR(12) NOT NULL,
			RequestedDate TIMESTAMP NOT NULL,
			TargetDate TIMESTAMP NOT NULL,
			Message VARCHAR(800) NOT NULL,
			User VARCHAR(80) NOT NULL
		)
	''')
	c.execute('''
		CREATE TABLE IF NOT EXISTS comments (
			ID INTEGER PRIMARY KEY AUTOINCREMENT,
			ThreadID VARCHAR(12) NOT NULL,
			CommentID VARCHAR(12) NOT NULL,
			CurrentCount INTEGER DEFAULT 1,
			SourceID VARCHAR(12) NOT NULL,
			TargetDate TIMESTAMP NOT NULL,
			UNIQUE (ThreadID)
		)
	''')
	dbConn.commit()


def close():
	dbConn.commit()
	dbConn.close()


def saveReminder(reminder):
	if not isinstance(reminder, Reminder):
		return False
	if reminder.id is not None:
		return False

	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO reminders
			(SourceID, RequestedDate, TargetDate, Message, User)
			VALUES (?, ?, ?, ?, ?)
		''', (reminder.sourceId,
		      reminder.requestedDate.strftime("%Y-%m-%d %H:%M:%S"),
		      reminder.targetDate.strftime("%Y-%m-%d %H:%M:%S"),
		      reminder.message,
		      reminder.user))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()

	return True


def getReminders():
	c = dbConn.cursor()
	results = []
	for row in c.execute('''
		SELECT ID, SourceID, RequestedDate, TargetDate, Message, User
		FROM reminders
		WHERE TargetDate < CURRENT_TIMESTAMP
		'''):
		reminder = Reminder()
		reminder.id = row[0]
		reminder.sourceId = row[1]
		reminder.requestedDate = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
		reminder.targetDate = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
		reminder.message = row[4]
		reminder.user = row[5]
		results.append(reminder)

	return results


def deleteReminder(reminder):
	if reminder.id is None:
		return False

	c = dbConn.cursor()
	c.execute('''
		DELETE FROM reminders
		WHERE ID = ?
	''', (reminder.id,))
	dbConn.commit()

	if c.rowcount == 1:
		return True
	else:
		return False
