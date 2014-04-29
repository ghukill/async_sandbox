import redis

r = redis.StrictRedis(host='localhost', port=6379, db="test")
r.set('foo', 'bar')