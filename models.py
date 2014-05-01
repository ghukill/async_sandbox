class jobBlob:	
	def __init__(self, job_num):
		self.job_num = job_num
		self.estimated_tasks = ''
		self.assigned_tasks = []	
		self.completed_tasks = []
		self.error_tasks = []
