import discord_logging

log = discord_logging.init_logging()

from database import Database

database = Database()
database.engine.execute("ALTER TABLE comments ADD COLUMN from_mention BOOLEAN NOT NULL DEFAULT 0")
database.close()
log.info("Added from_mention column to comments table")
