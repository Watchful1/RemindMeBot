import re

LOG_FOLDER_NAME = "logs"
USER_AGENT = "RemindMeBot (by /u/Watchful1)"
OWNER = "Watchful1"
DATABASE_NAME = "database.db"
MESSAGE_LINK = "https://www.reddit.com/message/messages/"
ACCOUNT_NAME = "RemindMeBot"
BACKUP_FOLDER_NAME = "backup"
BLACKLISTED_ACCOUNTS = ['[deleted]', 'kzreminderbot', 'AutoModerator', 'remindditbot','chaintip']
RECURRING_LIMIT = 30

TRIGGER = "RemindMe"
TRIGGER_LOWER = TRIGGER.lower()
TRIGGER_SPLIT = "Remind Me"
TRIGGER_SPLIT_LOWER = TRIGGER_SPLIT.lower()
TRIGGER_RECURRING = "RemindMeRepeat"
TRIGGER_RECURRING_LOWER = TRIGGER_RECURRING.lower()
TRIGGER_CAKEDAY = "Cakeday"
TRIGGER_CAKEDAY_LOWER = TRIGGER_CAKEDAY.lower()
TRIGGER_COMBINED = f"{TRIGGER_LOWER}|{TRIGGER_CAKEDAY_LOWER}|{TRIGGER_RECURRING_LOWER}|%22{TRIGGER_SPLIT_LOWER.replace(' ', '%20')}%22"

CAKEDAY_MESSAGE = "Happy Cakeday!"

INFO_POST = "https://www.reddit.com/r/RemindMeBot/comments/e1bko7/remindmebot_info_v21/"
INFO_POST_REPEAT = "https://www.reddit.com/r/RemindMeBot/comments/e1a9rt/remindmerepeat_info_post/"
INFO_POST_CAKEDAY = "https://www.reddit.com/r/RemindMeBot/comments/e0tgoj/cakeday_info_post/"
INFO_POST_SETTINGS = "https://www.reddit.com/r/RemindMeBot/comments/e1asdu/timezone_and_clock_info_post/"
INFO_POST_MENTION = ""

MENTION_DETECTION_ENABLED = True
MENTION_DETECTION_WARN = True
MENTION_REMINDERS_ENABLED = False
ENCOURAGE_MENTIONS_IN_REPLY = False

MENTION_PATTERN = None  # populated by set_account_name below


def set_account_name(name):
	global ACCOUNT_NAME, MENTION_PATTERN
	ACCOUNT_NAME = name
	MENTION_PATTERN = re.compile(
		rf"/?u/{re.escape(name.lower())}(?:\s+(repeat|cakeday))?\b"
	)


set_account_name(ACCOUNT_NAME)
