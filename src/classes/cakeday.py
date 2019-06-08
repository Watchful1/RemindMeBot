import utils
import static


class Cakeday:
	def __init__(
		self,
		user,
		date_time,
		db_id=None
	):
		self.user = user
		self.date_time = date_time
		self.db_id = db_id

	def render_confirmation(self):
		bldr = utils.str_bldr()
		bldr.append("I will message you every year at ")
		bldr.append(utils.render_time(self.date_time, "%m-%d %H:%M:%S %Z"))
		bldr.append(" to remind you of your cakeday.")

		bldr.append("\n\n")

		bldr.append("[Click here](")
		bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Delete Cakeday Reminder", "Delete! cakeday"))
		bldr.append(") to delete this reminder.")

		return bldr

	def render_notification(self):
		bldr = utils.str_bldr()
		bldr.append("Happy cakeday!")

		bldr.append("\n\n")

		bldr.append("I will message you every year at ")
		bldr.append(utils.render_time(self.date_time, "%m-%d %H:%M:%S %Z"))
		bldr.append(" to remind you of your cakeday.")

		bldr.append("\n\n")

		bldr.append("[Click here](")
		bldr.append(utils.build_message_link(static.ACCOUNT_NAME, "Remove Cakeday Reminder", "Remove! cakeday"))
		bldr.append(") to delete this reminder.")

		return bldr
