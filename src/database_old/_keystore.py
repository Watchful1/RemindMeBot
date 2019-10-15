import discord_logging


log = discord_logging.get_logger()


class _DatabaseKeystore:
	def __init__(self):
		self.dbConn = self.dbConn  # for pycharm linting

	def save_keystore(self, key, value):
		log.debug(f"Saving keystore: {key} : {value}")
		c = self.dbConn.cursor()
		c.execute('''
			REPLACE INTO keystore
			(Key, Value)
			VALUES (?, ?)
		''', (key, value))
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
