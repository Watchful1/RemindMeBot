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
from ._users import _DatabaseUsers
from ._stats import _DatabaseStats

log = discord_logging.get_logger()


def abort_ro(*args,**kwargs):
	return


class Database(_DatabaseReminders, _DatabaseComments, _DatabaseKeystore, _DatabaseSubreddit, _DatabaseUsers, _DatabaseStats):
	def __init__(self, debug=False, publish=False, override_location=None, readonly=False, quiet=False):
		if not quiet:
			log.info(f"Initializing database class: debug={debug} publish={publish}")
		self.debug = debug
		self.engine = None
		self.init(debug, publish, override_location, readonly)

		_DatabaseReminders.__init__(self)
		_DatabaseComments.__init__(self)
		_DatabaseKeystore.__init__(self)
		_DatabaseSubreddit.__init__(self)
		_DatabaseUsers.__init__(self)
		_DatabaseStats.__init__(self)

	def init(self, debug, publish, override_location=None, readonly=False):
		if debug:
			self.engine = create_engine(f'sqlite:///:memory:')
		else:
			if override_location:
				self.engine = create_engine(f'sqlite:///{override_location}')
			else:
				self.engine = create_engine(f'sqlite:///{static.DATABASE_NAME}')

		Session = sessionmaker(bind=self.engine)
		self.session = Session()
		if readonly:
			self.session.flush = abort_ro
			self.session._flush = abort_ro

		if publish:
			Base.metadata.drop_all(self.engine)

		Base.metadata.create_all(self.engine)

		self.commit()

	def backup(self):
		log.info("Backing up database")
		self.commit()
		self.close()

		if not os.path.exists(static.BACKUP_FOLDER_NAME):
			os.makedirs(static.BACKUP_FOLDER_NAME)

		copyfile(
			static.DATABASE_NAME,
			static.BACKUP_FOLDER_NAME + "/" + utils.datetime_now().strftime("%Y-%m-%d_%H-%M") + ".db")

		self.init(self.debug, False)

	def commit(self):
		self.session.commit()

	def close(self):
		self.session.commit()
		self.engine.dispose()
