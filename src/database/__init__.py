from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import discord_logging
from shutil import copyfile

Base = declarative_base()

import static
import utils
from ._keystore import _DatabaseKeystore
from ._reminders import _DatabaseReminders
from ._comments import _DatabaseComments
from ._subreddits import _DatabaseSubreddit
from ._user_settings import _DatabaseUserSettings

log = discord_logging.get_logger()


class Database(_DatabaseReminders, _DatabaseComments, _DatabaseKeystore, _DatabaseSubreddit, _DatabaseUserSettings):
	def __init__(self, debug=False, publish=False, clone=False):
		log.info(f"Initializing database class: debug={debug} publish={publish} clone={clone}")
		self.debug = debug
		self.init(debug, publish, clone)
		self.engine = None

		_DatabaseReminders.__init__(self)
		_DatabaseComments.__init__(self)
		_DatabaseKeystore.__init__(self)
		_DatabaseSubreddit.__init__(self)
		_DatabaseUserSettings.__init__(self)

	def init(self, debug, publish, clone):
		if debug:
			if clone:
				if os.path.exists(static.DATABASE_DEBUG_NAME):
					os.remove(static.DATABASE_DEBUG_NAME)
				copyfile(static.DATABASE_NAME, static.DATABASE_DEBUG_NAME)

			self.engine = create_engine(f'sqlite:///{static.DATABASE_DEBUG_NAME}')
		else:
			self.engine = create_engine(f'sqlite:///{static.DATABASE_NAME}')

		Session = sessionmaker(bind=self.engine)
		self.session = Session()

		if publish:
			Base.metadata.drop_all(self.engine)

		Base.metadata.create_all(self.engine)

		if self.get_keystore("remindme_comment") is None:
			self.save_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

		self.commit()

	def backup(self):
		log.info("Backing up database")
		self.commit()
		self.engine.dispose()

		if not os.path.exists(static.BACKUP_FOLDER_NAME):
			os.makedirs(static.BACKUP_FOLDER_NAME)
		copyfile(
			static.DATABASE_NAME,
			static.BACKUP_FOLDER_NAME + "/" + utils.datetime_now().strftime("%Y-%m-%d_%H-%M") + ".db")

		self.init(self.debug, False, False)

	def commit(self):
		self.session.commit()
