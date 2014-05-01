import models

from flask import Flask, render_template, g
import redis
from celery import Celery
import time
import json
import pickle

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


#prepare handle to redis for batching jobs
r_batch_handle = redis.StrictRedis(host='localhost', port=6379, db=2)


@celery.task()
def add_together(a, b, count):
	print "Starting:",count
	time.sleep(.5)
	return a + b


@app.route("/")
# @app.route("/<user>/<job>")
def index():
	print "Starting request..."
	# celery task deploying
	count = 0
	task_num = 100
	results = {}

	# increment and get job num
	# NOTE: can use this job num to create log file - ALL jobs will increment counter by one, so logs will always be unique
	job_num = r_batch_handle.incr("job_num")
	print "Beginning job #",job_num

	jobHand = models.jobBlob(job_num)	
	# jobHand.job_num = job_num

	'''
	Okay, here's the deal.  We're going to create a dictionary / list what have you, push the resulting task_id and associate it with the job_num.
	I thought Jobtastic does this, but I think it's designed for monitoring a single task.
		- thought: we could have bulk tasks go through a single celery task, essentially wrapping 10,000 jobs into a burrito that celery eats
		- in that way, we could pretty easily get a completion graph.  
		- but not great, lose granularity of each task, whether or not celery thinks, no KNOWS, if it failed
	We create this blob that has the job_num and all the task_id's associated with it, then stick it "somewhere".
	This can be read on the front-end, should be associated with user / session.

	To figure out if the job / job_num is "complete", will have to itererate through items and run 
		result = celery.AsyncResult(task_id)
		state = result.state
		If these all say "SUCCESS", then done!

	NOTES:
		- consider dropping the "count", probably don't need
	'''
	def goober():
		print "WOAH NELLY!"

	jobHand.estimated_tasks = task_num	
	while count < task_num:		
		result = add_together.delay(23, 42, count)
		# jobHand.assigned_tasks.append((count,result))
		jobHand.assigned_tasks.append(str(result))
		print count, result		
		results[count] = str(result)
		count += 1		
	print "Finished job #",job_num	

	# push jobBlob to redis /2 / need to pickle first
	jobHand_pickled = pickle.dumps(jobHand)
	r_batch_handle.set("job_{job_num}".format(job_num=job_num),jobHand_pickled)

	return "You have initiated job {job_num}.  Click <a href='/job_status/{job_num}'>here</a> to check it foo.".format(job_num=job_num)

@app.route("/task_status/<task_id>")
def task_status(task_id):
	
	# global way to surgically pick task out of celery memory,
	# below, we're actually saving the Async objects in Redis!
	# WOAH - probably the same real deep down....
	result = celery.AsyncResult(task_id)	
	state, retval = result.state, result.result
	response_data = dict(id=task_id, status=state, result=retval)
	
	return json.dumps(response_data)


	return "You are looking for {task_id}".format(task_id=task_id)	



@app.route("/job_status/<job_num>")
def job_status(job_num):	

	'''
	There is an element of analysis to this, WHERE this happens will be important.
	Example this check is working nicely only when it runs to refresh
		- polling might take care of a lot of this..

	Improvements:
		- first shunts assigned_tasks to pending and completed
		- then, only do pending, checks get faster each time

	* Not a lot of sense of doing too much optimizing here, will be breaking these out soon enough
	'''
	
	# retrieving and unpickling from redis	
	jobHand_pickled = r_batch_handle.get("job_{job_num}".format(job_num=job_num))
	jobHand = pickle.loads(jobHand_pickled)	
	
	if len(jobHand.completed_tasks) == 0:
		return "Job Queued, waiting for others to finish."

	# if length of completed == assigned, then already checked and skip below	
	if len(jobHand.completed_tasks) == len(jobHand.assigned_tasks):
		return "Job Complete!"

	# else, get status of job
	jobHand.completed_tasks = []
	for task in jobHand.assigned_tasks:
		print "Checking task:",task
		result = celery.AsyncResult(task)				
		state = result.state
		print "Status:",state

		if state == "SUCCESS":
			jobHand.completed_tasks.append(task)


	# update job in redis	
	jobHand_pickled = pickle.dumps(jobHand)
	r_batch_handle.set("job_{job_num}".format(job_num=job_num),jobHand_pickled)

	# check status	
	return "{completed} / {total} Completed.".format(completed=len(jobHand.completed_tasks),total=len(jobHand.assigned_tasks))

	return "failsafe"