Welcome to the newly redesigned RemindMeBot!
====================================

u/RemindMeBotWrangler agreed to let me take over the bot since he didn't have time to keep it up anymore. I have fully rewritten the code to be more stable, faster and with a couple extra features.

Right now, the new version of the bot is running under the test account u/Watchful1BotTest, using ReminderTest! instead of RemindMe!. I'm hoping to get a few people using it to iron out the bugs, and then I'll copy all the reminders over and switch it back to the main account. I'll keep running the old version under the main account until then.

**Parsing library:** The old bot used the [parsedatetime](https://github.com/bear/parsedatetime) library, which is no longer updated. The new version uses [dateparser](https://github.com/scrapinghub/dateparser), which is much more comprehensive, supporting things like timezones, and even foreign languages.

**Cakeday:** You can now message the bot "Cakeday!" and it will send you a notification each year on your cakeday, until you tell it to stop.

*****

**What is RemindMeBot?**

RemindMeBot is a reddit bot that lets you set a reminder for a certain amount of time, via a comment or private message, and then sends you a reminder message at your targeted time. Use it if you want to check back on a thread for updates, or remember to do something a week from now.

**RemindMeBot commands**

Only the RemindMe! command can be done in a comment, all others must be private messaged to the bot.

1. **RemindMe! 3 days** Create a reminder for the specified amount of time. This can be done by posting a comment, or private messaging the bot. You can include a message by adding it surrounded by [] or "". If you are private messaging the bot, a message is recommended so you remember what the notification is about.
2. **MyReminders!** Replies with a list of your reminders, including links to delete them.
3. **Remove! 123** Cancels the specified reminder. The numbers are automatically filled in when you click the message link from the MyReminders message list.
4. **RemoveAll!** Cancel all of your reminders.
5. **Delete! 123** Delete a comment from the RemindMeBot. The numbers are automatically filled in when you click a delete link in the comment. This only works if you are the person the bot was replying to.
6. **Cakeday!** Set up a reminder each year on your cakeday.

**Date Options**

If the time is: 2014-06-01 01:37:35 UTC

Time Option | New Time
---------|----------
RemindMe! One Year | 2015-06-01 01:37:35 UTC
RemindMe! 3 Months | 2014-09-01 01:37:35 UTC
RemindMe! One Week | 2014-06-08 01:37:35 UTC
RemindMe! 1 Day | 2014-06-02 01:37:35 UTC
RemindMe! 33 Hours | 2014-06-02 10:37:35 UTC
RemindMe! 10 Minutes | 2014-06-01 01:47:35 UTC
RemindMe! August 25th, 2014 | 2014-08-25 01:37:35 UTC
RemindMe! 25 Aug 2014 | 2014-08-25 01:37:35 UTC
RemindMe! 5pm August 25 | **2014-08-25 17:00:00 UTC**
RemindMe! Next Saturday | **2014-06-14 09:00:00 UTC**
RemindMe! Tomorrow | **2014-06-02 09:00:00 UTC**
RemindMe! Next Thursday at 4pm | **2014-06-12 16:00:00 UTC**
RemindMe! Tonight | **2014-06-01 21:00:00 UTC**
RemindMe! at 4pm | **2014-06-01 16:00:00 UTC**
RemindMe! 2 Hours After Noon | **2014-06-01 14:00:00 UTC**
RemindMe! eoy | **2014-12-31 09:00:00 UTC**
RemindMe! eom | **2014-06-30 09:00:00 UTC**
RemindMe! eod | **2014-06-01 17:00:00 UTC**

**Message links**

RemindMeBot makes use of prefilled message links, like [this one](https://www.reddit.com/message/compose/?to=RemindMeBot&subject=Test&message=Test). From my research, these links work correctly in the browser on the classic site, the redesign, the mobile web site, and every single reddit app, except the official iOS reddit app. If you are on iOS, you can open the link in your mobile browser, switch to a different reddit app, or wait till you're on a computer browser.

If you think links like these should work in the iOS app, feel free to make a post about it in r/redditmobile.

**Chat support**

The reddit API currently does not support the chat. There are ways around this so bots can use the chat even though the API doesn't support it, but they are a bit harder to use. I'll hopefully be able to add support soon. The bot currently has 13600 unread chat notifications, so it sounds like it will be a popular feature.

**Source**

The bot is open source:

https://github.com/Watchful1/RemindMeBot
