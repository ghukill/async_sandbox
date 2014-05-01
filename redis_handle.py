import redis

def redis_handle(db_num):
	return redis.StrictRedis(host='localhost', port=6379, db=db_num)
