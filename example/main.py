
import api
from apiserv import Server
import redis


redis_obj = redis.StrictRedis()


s = Server(
	redis=redis_obj,
	api=api,
	raise_=False)

s.mainloop(bind=("localhost", 8080))




