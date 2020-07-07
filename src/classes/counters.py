import prometheus_client


class Counters:
	def __init__(self):
		self.messages_replied = prometheus_client.Counter('messages_replied', "Count of messages replied to")
		self.comments_replied = prometheus_client.Counter('comments_replied', "Count of comments replied to")
		self.notifications_sent = prometheus_client.Counter('notifications_sent', "Count of notifications sent")
		self.queue_size = prometheus_client.Gauge('queue_size', "Current queue size")

		self.trigger_comment_single = prometheus_client.Counter('trigger_comment_single', "Count of remindme comments")
		self.trigger_comment_split = prometheus_client.Counter('trigger_comment_split', "Count of remind me comments")
		self.trigger_comment_cake = prometheus_client.Counter('trigger_comment_cake', "Count of cakeday comments")
		self.trigger_comment_repeat = prometheus_client.Counter('trigger_comment_repeat', "Count of remindmerepeat comments")

		self.count_total = prometheus_client.Gauge('count_objects', "Current total number of reminders")
		self.pushshift_age = prometheus_client.Gauge('pushshift_age', "Current pushshift delay in minutes")

	@staticmethod
	def start_server(port):
		prometheus_client.start_http_server(port)
