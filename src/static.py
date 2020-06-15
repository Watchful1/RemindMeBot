LOG_FOLDER_NAME = "logs"
USER_AGENT = "RemindMeBot (by /u/Watchful1)"
OWNER = "Watchful1"
DATABASE_NAME = "database.db"
MESSAGE_LINK = "https://www.reddit.com/message/messages/"
ACCOUNT_NAME = "Watchful1BotTest"
BACKUP_FOLDER_NAME = "backup"
BLACKLISTED_ACCOUNTS = ['[deleted]', 'kzreminderbot', 'AutoModerator', 'remindditbot']
RECURRING_LIMIT = 30

TRIGGER = "RemindMe"
TRIGGER_LOWER = TRIGGER.lower()
TRIGGER_SPLIT = "Remind Me"
TRIGGER_SPLIT_LOWER = TRIGGER_SPLIT.lower()
TRIGGER_RECURRING = "RemindMeRepeat"
TRIGGER_RECURRING_LOWER = TRIGGER_RECURRING.lower()
TRIGGER_CAKEDAY = "Cakeday"
TRIGGER_CAKEDAY_LOWER = TRIGGER_CAKEDAY.lower()
TRIGGER_COMBINED = f"{TRIGGER_LOWER}|{TRIGGER_CAKEDAY_LOWER}|{TRIGGER_RECURRING_LOWER}|{TRIGGER_SPLIT_LOWER}"

CAKEDAY_MESSAGE = "Happy Cakeday!"

INFO_POST = "https://www.reddit.com/r/RemindMeBot/comments/e1bko7/remindmebot_info_v21/"
INFO_POST_REPEAT = "https://www.reddit.com/r/RemindMeBot/comments/e1a9rt/remindmerepeat_info_post/"
INFO_POST_CAKEDAY = "https://www.reddit.com/r/RemindMeBot/comments/e0tgoj/cakeday_info_post/"
INFO_POST_SETTINGS = "https://www.reddit.com/r/RemindMeBot/comments/e1asdu/timezone_and_clock_info_post/"
