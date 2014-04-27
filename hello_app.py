from flask import Flask, render_template, g
import time
from celery import Celery

def make_celery(app):
	celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
	celery.conf.update(app.config)
	TaskBase = celery.Task
	class ContextTask(TaskBase):
		abstract = True
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return TaskBase.__call__(self, *args, **kwargs)
	celery.Task = ContextTask
	return celery

app = Flask(__name__)

# celery updates
app.config.update(
	CELERY_BROKER_URL='redis://localhost:6379/0',
	CELERY_RESULT_BACKEND='redis://localhost:6379/1'
)



celery = make_celery(app)


@app.route("/")
def index():
	print "Starting request..."

	# celery task deploying
	count = 0
	while count < 30:
		result = add_together.delay(23, 42, count)
		print result
		count += 1	

	print "Finished sleeping, returning response."
	return "Hello World!  Celery tasks deployed foo."

@celery.task()
def add_together(a, b, count):
	print "Starting:",count
	time.sleep(1)
	return a + b