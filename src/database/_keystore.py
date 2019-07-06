import sqlite3
import discord_logging


log = discord_logging.get_logger()


class _DatabaseKeystore:
	def __init__(self):
		self.dbConn = self.dbConn  # for pycharm linting

	def save_keystore(self, key, value):
		log.debug(f"Saving keystore: {key} : {value}")
		c = self.dbConn.cursor()
		try:
			c.execute('''
				INSERT INTO keystore
				(Key, Value)
				VALUES (?, ?)
			''', (key, value))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to save keystore: {err}")
			return False

		self.dbConn.commit()

		return True

	def update_keystore(self, key, value):
		log.debug(f"Updating keystore: {key} : {value}")
		c = self.dbConn.cursor()
		try:
			c.execute('''
				UPDATE keystore
				SET Value = ?
				WHERE Key = ?
			''', (value, key))
		except sqlite3.IntegrityError as err:
			log.warning(f"Failed to update keystore: {err}")
			return False

		self.dbConn.commit()

		return True

	def get_keystore(self, key):
		log.debug(f"Fetching keystore: {key}")
		c = self.dbConn.cursor()
		c.execute('''
			SELECT Value
			FROM keystore
			WHERE Key = ?
			''', (key,))

		result = c.fetchone()
		if result is None or len(result) == 0:
			log.debug("Key not found")
			return None

		log.debug(f"Value: {result[0]}")
		return result[0]

	def delete_keystore(self, key):
		log.debug(f"Deleting key: {key}")
		c = self.dbConn.cursor()
		c.execute('''
			DELETE FROM keystore
			WHERE Key = ?
		''', (key,))
		self.dbConn.commit()

		if c.rowcount == 1:
			log.debug("Key deleted")
			return True
		else:
			log.debug("Key not deleted")
			return False