from reminder import Reminder
import reddit

def processMessages():
	for message in reddit.getMessages():
		body = message.body.lower()
		if "remindme" in body[:8]:


