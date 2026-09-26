# RemindMeBot

This is the code for [u/RemindMeBot](https://www.reddit.com/user/RemindMeBot) on Reddit. Comment `RemindMe! 2 weeks` and the bot replies to confirm, then messages you when the time's up. It also supports recurring reminders, cake day reminders, and per-user time zones ([info post](https://www.reddit.com/r/RemindMeBot/comments/e1bko7/remindmebot_info_v21/)).

I took it over from u/RemindMeBotWrangler in 2019 and rewrote it. It has about 1.1 million pending reminders and sends around 3,000 a day. I'm currently porting it to Reddit's [Devvit](https://developers.reddit.com/) platform in TypeScript.

## How it works

It's one Python process running in a loop. It reads its inbox, picks up new comments with a trigger word, saves any new reminders, and sends whatever is due. Every 30 minutes it edits old confirmation comments whose "N others will be reminded" count is out of date, and every hour it updates stats and the r/AskHistorians `remindme` wiki page.

Comments come from a separate ingest process (not in this repo) that writes matching comments to a SQLite file passed in with `--ingest_db`. Without that, the bot only handles messages and username mentions.

Times go through `dateparser.parse`, then dateparser's `search_dates`, then parsedatetime, and are converted to the user's time zone.

## Tech

Python, SQLAlchemy on SQLite, and PRAW through [PrawWrapper](https://github.com/Watchful1/PrawWrapper), which also gives the pytest suite a fake Reddit to run against. Dates are parsed with a [fork of dateparser](https://github.com/Watchful1/dateparser) and [parsedatetime](https://github.com/bear/parsedatetime). Errors get posted to Discord with [DiscordLogging](https://github.com/Watchful1/DiscordLogging), and it exports Prometheus metrics.

## License

This code is published for reference. All rights reserved; please don't run your own copy of the bot.
