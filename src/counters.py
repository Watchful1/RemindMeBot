import prometheus_client

replies = prometheus_client.Counter('bot_replies', "Count of objects replied to", ['source', 'type'])
notifications = prometheus_client.Counter('bot_sent', "Count of notifications sent")
queue = prometheus_client.Gauge('bot_queue', "Current queue size")
objects = prometheus_client.Gauge('bot_objects', "Total number of active reminders")
pushshift_delay = prometheus_client.Gauge('bot_pushshift_minutes', "Pushshift delay in minutes", ['client'])
pushshift_failed = prometheus_client.Gauge('bot_pushshift_failed', "Pushshift timeout status", ['client'])
pushshift_client = prometheus_client.Gauge('bot_pushshift_client', "Which pushshift client is being used", ['client'])
errors = prometheus_client.Counter('bot_errors', "Count of errors", ['type'])


def init(port):
	prometheus_client.start_http_server(port)
