import re
from datetime import datetime
from datetime import timezone
import dateparser


def findMessage(body):
	messages = re.findall('(?:\[)(.*?)(?:\])', body)
	if len(messages) > 0:
		return messages[0]
	else:
		return None


def findTime(body):
	times = re.findall('(?:remindme.? )(.*)', body)
	if len(times) > 0:
		return times[0]
	else:
		return None


def parseTime(time):
	return None




def parse_comment(self):
	dateparser.parse("3 days")
	# Use message default if not found
	messageInputTemp = re.search('(["].{0,9000}["])', tempString)
	if messageInputTemp:
		self._messageInput = messageInputTemp.group()
	# Fix issue with dashes for parsedatetime lib
	tempString = tempString.replace('-', "/")
	# Remove RemindMe!
	self._storeTime = re.sub('(["].{0,9000}["])', '', tempString)[9:]

def save_to_db(self):
	"""
	Saves the permalink comment, the time, and the message to the DB
	"""

	cal = pdt.Calendar()
	try:
		holdTime = cal.parse(self._storeTime, datetime.now(timezone('UTC')))
	except Exception:
		# year too long
		holdTime = cal.parse("9999-12-31")
	if holdTime[1] == 0:
		# default time
		holdTime = cal.parse("1 day", datetime.now(timezone('UTC')))
		self._replyMessage = "**Defaulted to one day.**\n\n"
	# Converting time
	# 9999/12/31 HH/MM/SS
	self._replyDate = time.strftime('%Y-%m-%d %H:%M:%S', holdTime[0])
	cmd = "INSERT INTO message_date (permalink, message, new_date, origin_date, userID) VALUES (%s, %s, %s, %s, %s)"
	self._addToDB.cursor.execute(cmd, (
		self.comment.permalink.encode('utf-8'),
		self._messageInput.encode('utf-8'),
		self._replyDate,
		self._originDate,
		self.comment.author))
	self._addToDB.connection.commit()
	# Info is added to DB, user won't be bothered a second time
	self.commented.append(self.comment.id)