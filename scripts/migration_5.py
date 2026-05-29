import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import discord_logging

log = discord_logging.init_logging()

from database import Database

database = Database()
with database.engine.connect() as conn:
	conn.exec_driver_sql("ALTER TABLE comments ADD COLUMN from_mention BOOLEAN NOT NULL DEFAULT 0")
	conn.commit()
database.close()
log.info("Added from_mention column to comments table")
