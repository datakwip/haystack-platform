# gunicorn.conf.py

# Server bind address and port
bind = '0.0.0.0:8000'

# Number of worker processes
workers = 4

# Number of threads per worker
threads = 2

# The logging level (debug, info, warning, error, critical)
loglevel = 'debug'

# Access log file
accesslog = 'access.log'

# Error log file
errorlog = 'error.log'

# Log format for access log
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# The timeout for workers
timeout = 30

# Whether to run Gunicorn in daemon mode (background)
daemon = False

# Worker class (sync, eventlet, gevent, etc.)
worker_class = 'sync'

# Preload the application (helps with faster startup)
preload_app = True

# Maximum number of requests a worker will handle before restarting
max_requests = 1000

# Number of maximum request errors before worker is restarted
max_requests_jitter = 50