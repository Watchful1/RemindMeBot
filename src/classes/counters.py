import prometheus_client


class Counters:
	def __init__(self):
		self.messages_replied = prometheus_client.Counter('messages_replied', "Count of messages replied to")
		self.comments_replied = prometheus_client.Counter('comments_replied', "Count of comments replied to")
		self.notifications_sent = prometheus_client.Counter('notifications_sent', "Count of notifications sent")
		self.queue_size = prometheus_client.Gauge('queue_size', "Current queue size")

	@staticmethod
	def start_server(port):
		prometheus_client.start_http_server(port)
