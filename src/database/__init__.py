from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import discord_logging
from shutil import copyfile

import static
import utils
from ._keystore import _DatabaseKeystore

log = discord_logging.get_logger()


Base = declarative_base()


class Database(_DatabaseKeystore):
	def __init__(self, debug=False, publish=False, clone=False):
		log.info(f"Initializing database class: debug={debug} publish={publish} clone={clone}")
		self.debug = debug
		self.dbConn = None
		self.init(debug, publish, clone)
		self.engine = None

		_DatabaseKeystore.__init__(self)

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

		c = self.dbConn.cursor()
		if publish:
			Base.metadata.drop_all(self.engine)

		Base.metadata.create_all(self.engine)

		if self.get_keystore("remindme_comment") is None:
			self.save_keystore("remindme_comment", utils.get_datetime_string(utils.datetime_now()))

		self.dbConn.commit()

	def backup(self):
		log.info("Backing up database")
		self.engine.dispose()

		if not os.path.exists(static.BACKUP_FOLDER_NAME):
			os.makedirs(static.BACKUP_FOLDER_NAME)
		copyfile(
			static.DATABASE_NAME,
			static.BACKUP_FOLDER_NAME + "/" + utils.datetime_now().strftime("%Y-%m-%d_%H-%M") + ".db")

		self.init(self.debug, False, False)
