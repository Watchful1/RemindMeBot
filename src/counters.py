import prometheus_client

replies = prometheus_client.Counter('bot_replies', "Count of objects replied to", ['source', 'type'])
notifications = prometheus_client.Counter('bot_sent', "Count of notifications sent")
queue = prometheus_client.Gauge('bot_queue', "Current queue size")
objects = prometheus_client.Gauge('bot_objects', "Total number of active reminders")
pushshift = prometheus_client.Gauge('bot_pushshift_minutes', "Pushshift delay in minutes")
errors = prometheus_client.Counter('bot_errors', "Count of errors", ['type'])


def init(port):
	prometheus_client.start_http_server(port)
