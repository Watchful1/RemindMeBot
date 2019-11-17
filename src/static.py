LOG_FOLDER_NAME = "logs"
USER_AGENT = "RemindMeBot (by /u/Watchful1)"
OWNER = "Watchful1"
DATABASE_NAME = "database.db"
MESSAGE_LINK = "https://www.reddit.com/message/messages/"
ACCOUNT_NAME = "Watchful1BotTest"
BACKUP_FOLDER_NAME = "backup"
BLACKLISTED_ACCOUNTS = ['[deleted]', 'kzreminderbot']
RECURRING_LIMIT = 30

TRIGGER = "ReminderTest"
TRIGGER_LOWER = TRIGGER.lower()
TRIGGER_RECURRING = "ReminderTestRepeat"
TRIGGER_RECURRING_LOWER = TRIGGER_RECURRING.lower()
TRIGGER_CAKEDAY = "CakedayTest"
TRIGGER_CAKEDAY_LOWER = TRIGGER_CAKEDAY.lower()
TRIGGER_COMBINED = f"{TRIGGER_LOWER}|{TRIGGER_CAKEDAY_LOWER}"

CAKEDAY_MESSAGE = "Happy Cakeday!"
