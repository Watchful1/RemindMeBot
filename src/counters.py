import prometheus_client

replies = prometheus_client.Counter('bot_replies', "Count of objects replied to", ['source', 'type'])
notifications = prometheus_client.Counter('bot_sent', "Count of notifications sent")
queue = prometheus_client.Gauge('bot_queue', "Current queue size")
objects = prometheus_client.Gauge('bot_objects', "Total number of objects by type", ['type'])
errors = prometheus_client.Counter('bot_errors', "Count of errors", ['type'])
run_time = prometheus_client.Summary('bot_run_seconds', "How long a full loop takes")


def init(port):
	prometheus_client.start_http_server(port)
