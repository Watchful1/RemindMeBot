import sqlite3
import discord_logging

from classes.reminder import Reminder
from classes.cakeday import Cakeday
import utils


log = discord_logging.get_logger()


class _DatabaseReminders:
	def __init__(self):
		self.dbConn = self.dbConn  # for pycharm linting

	def save_reminder(self, reminder):
		if not isinstance(reminder, Reminder):
			return False

		c = self.dbConn.cursor()
		if reminder.db_id is not None:
			log.debug(f"Updating reminder: {reminder.db_id}")
			try:
				c.execute('''
					UPDATE reminders
					SET Source = ?,
						RequestedDate = ?,
						TargetDate = ?,
						Message = ?,
						User = ?,
						Defaulted = ?
					WHERE ID = ?
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.defaulted,
					reminder.db_id))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to update reminder: {err}")
				return False
		else:
			log.debug("Saving new reminder")
			try:
				c.execute('''
					INSERT INTO reminders
					(Source, RequestedDate, TargetDate, Message, User, Defaulted)
					VALUES (?, ?, ?, ?, ?, ?)
				''', (
					reminder.source,
					utils.get_datetime_string(reminder.requested_date),
					utils.get_datetime_string(reminder.target_date),
					reminder.message,
					reminder.user,
					reminder.defaulted))
			except sqlite3.IntegrityError as err:
				log.warning(f"Failed to save reminder: {err}")
				return False

			if c.lastrowid is not None:
				reminder.db_id = c.lastrowid
				log.debug(f"Saved to: {reminder.db_id}")

		self.dbConn.commit()

		return True

	def get_count_pending_reminders(self, timestamp):
		log.debug("Fetching count of pending reminders")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT COUNT(*)
			FROM reminders
			WHERE TargetDate < ?
			''', (utils.get_datetime_string(timestamp),))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No pending reminders")
			return 0

		log.debug(f"Count reminders: {result[0]}")
		return result[0]

	def get_pending_reminders(self, count, timestamp):
		log.debug("Fetching pending reminders")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT rm.ID, rm.Source, rm.RequestedDate, rm.TargetDate, rm.Message, rm.User, rm.Defaulted, us.TimeZone
			FROM reminders rm
				LEFT JOIN user_settings us
					ON us.User = rm.User
			WHERE rm.TargetDate < ?
			ORDER BY rm.TargetDate
			LIMIT ?
			''', (utils.get_datetime_string(timestamp), count)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				defaulted=row[6] == 1,
				timezone=row[7]
			)
			results.append(reminder)

		log.debug(f"Found reminders: {len(results)}")
		return results

	def get_user_reminders(self, username):
		log.debug(f"Fetching reminders for u/{username}")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT rm.ID, rm.Source, rm.RequestedDate, rm.TargetDate, rm.Message, rm.User, rm.Defaulted, us.TimeZone
			FROM reminders rm
				LEFT JOIN user_settings us
					ON us.User = rm.User
			WHERE rm.User = ?
			ORDER BY TargetDate
			''', (username,)):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				defaulted=row[6] == 1,
				timezone=row[7]
			)
			results.append(reminder)

		log.debug(f"Found reminders: {len(results)}")
		return results

	def get_reminder(self, reminder_id):
		log.debug(f"Fetching reminder by id: {reminder_id}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT rm.ID, rm.Source, rm.RequestedDate, rm.TargetDate, rm.Message, rm.User, rm.Defaulted, us.TimeZone
			FROM reminders rm
				LEFT JOIN user_settings us
					ON us.User = rm.User
			WHERE rm.ID = ?
			''', (reminder_id,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Reminder not found")
			return None

		reminder = Reminder(
			source=result[1],
			target_date=utils.parse_datetime_string(result[3]),
			message=result[4],
			user=result[5],
			db_id=result[0],
			requested_date=utils.parse_datetime_string(result[2]),
			defaulted=result[6] == 1,
			timezone=result[7]
		)

		return reminder

	def delete_reminder(self, reminder):
		log.debug(f"Deleting reminder by id: {reminder.db_id}")
		if reminder.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM reminders
			WHERE ID = ?
		''', (reminder.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Reminder deleted")
			return True
		else:
			log.debug("Reminder not deleted")
			return False

	def delete_user_reminders(self, user):
		log.debug(f"Deleting all reminders for u/{user}")
		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM reminders
			WHERE User = ?
		''', (user,))
		self.dbConn.commit()

		return c.rowcount

	def get_all_reminders(self):
		log.debug(f"Fetching all reminders")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT rm.ID, rm.Source, rm.RequestedDate, rm.TargetDate, rm.Message, rm.User, rm.Defaulted, us.TimeZone
			FROM reminders rm
				LEFT JOIN user_settings us
					ON us.User = rm.User
			ORDER BY TargetDate
			'''):
			reminder = Reminder(
				source=row[1],
				target_date=utils.parse_datetime_string(row[3]),
				message=row[4],
				user=row[5],
				db_id=row[0],
				requested_date=utils.parse_datetime_string(row[2]),
				defaulted=row[6] == 1,
				timezone=row[7]
			)
			results.append(reminder)

		log.debug(f"Found reminders: {len(results)}")
		return results

	def add_cakeday(self, cakeday):
		if cakeday.db_id is not None:
			log.warning(f"This cakeday already exists: {cakeday.db_id}")

		c = self.dbConn.cursor()
		log.debug("Saving new cakeday")
		try:
			c.execute('''
				INSERT INTO cakedays
				(CakedayDate, User)
				VALUES (?, ?)
			''', (
				utils.get_datetime_string(cakeday.date_time),
				cakeday.user))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save cakeday: {err}")
			return False

		if c.lastrowid is not None:
			cakeday.db_id = c.lastrowid
			log.debug(f"Saved to: {cakeday.db_id}")

		self.dbConn.commit()

		return True

	def delete_cakeday(self, cakeday):
		log.debug(f"Deleting cakeday by id: {cakeday.db_id}")
		if cakeday.db_id is None:
			return False

		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM cakedays
			WHERE ID = ?
		''', (cakeday.db_id,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Cakeday deleted")
			return True
		else:
			log.debug("Cakeday not deleted")
			return False

	def bump_cakeday(self, cakeday):
		if cakeday.db_id is None:
			log.warning(f"This cakeday doesn't exist: {cakeday.user}")

		c = self.dbConn.cursor()
		log.debug("Bumping cakeday one year")
		try:
			c.execute('''
				UPDATE cakedays
				SET CakedayDate = ?
				WHERE ID = ?
			''', (
				utils.get_datetime_string(utils.add_years(cakeday.date_time, 1)),
				cakeday.db_id))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to bump cakeday: {err}")
			return False

		self.dbConn.commit()

		return True

	def get_cakeday(self, user):
		log.debug(f"Fetching cake by user: {user}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT ID, CakedayDate, User
			FROM cakedays
			WHERE User = ?
			''', (user,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Cakeday not found")
			return None

		cakeday = Cakeday(
			user=result[2],
			date_time=utils.parse_datetime_string(result[1]),
			db_id=result[0]
		)

		return cakeday

	def get_count_pending_cakedays(self, timestamp):
		log.debug("Fetching count of pending cakedays")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT COUNT(*)
			FROM cakedays
			WHERE CakedayDate < ?
			''', (utils.get_datetime_string(timestamp),))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("No pending cakedays")
			return 0

		log.debug(f"Count cakedays: {result[0]}")
		return result[0]

	def get_pending_cakedays(self, count, timestamp):
		log.debug("Fetching pending cakedays")
		c = self.dbConn.cursor()
		results = []
		for row in c.execute('''
			SELECT ID, CakedayDate, User
			FROM cakedays
			WHERE CakedayDate < ?
			ORDER BY CakedayDate ASC
			LIMIT ?
			''', (utils.get_datetime_string(timestamp), count)):
			cakeday = Cakeday(
				user=row[2],
				date_time=utils.parse_datetime_string(row[1]),
				db_id=row[0]
			)
			results.append(cakeday)

		log.debug(f"Found cakedays: {len(results)}")
		return results