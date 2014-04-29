from flask import Flask, render_template, g

from celery import Celery

import time
import json

def make_celery(app):
	celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
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
app.debug = True

# celery updates
app.config.update(
	CELERY_BROKER_URL='redis://localhost:6379/0',
	CELERY_RESULT_BACKEND='redis://localhost:6379/1',
	CELERY_RESULT_SERIALIZER='json',
)

celery = make_celery(app)
@celery.task()
def add_together(a, b, count):
	print "Starting:",count
	time.sleep(.1)
	return a + b


@app.route("/")
# @app.route("/<user>/<job>")
def index():
	print "Starting request..."
	# celery task deploying
	count = 0
	results = {}
	while count < 100:
		result = add_together.delay(23, 42, count)
		print count, result
		results[count] = str(result)
		count += 1		
	print "Finished sleeping, returning response."	
	return json.dumps(results)


@app.route("/status/<task_id>")
def status(task_id):
	
	'''
	How do we access the celery thing here?
	'''
	print dir(celery)

	result = celery.AsyncResult(task_id)
	state, retval = result.state, result.result
	response_data = dict(id=task_id, status=state, result=retval)
	
	return json.dumps(response_data)


	return "You are looking for {task_id}".format(task_id=task_id)
	
