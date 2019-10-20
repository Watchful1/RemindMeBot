import discord_logging

from classes.key_value import KeyValue

log = discord_logging.get_logger()


class _DatabaseKeystore:
	def __init__(self):
		self.session = self.session  # for pycharm linting

	def save_keystore(self, key, value):
		log.debug(f"Saving keystore: {key} : {value}")
		self.session.merge(KeyValue(key, value))

	def get_keystore(self, key):
		log.debug(f"Fetching keystore: {key}")
		key_value = self.session.query(KeyValue).filter_by(key=key).first()

		if key_value is None:
			log.debug("Key not found")
			return None

		log.debug(f"Value: {key_value.value}")
		return key_value.value
