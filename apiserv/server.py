#!/usr/bin/env python


#gevent

from gevent import monkey; monkey.patch_all()
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace


#bottlepy and others

from bottle import * 
import json
from random import choice
from string import ascii_letters
import traceback
from pprint import pformat

#custom libs
from socketioshare import SimpleSocketIOShare


try:
	from taglog import log_with_tags
except ImportError:
	def log(msg, tags=["apiserv"]):
		print "{}: {}"",".format(",".join(tags), msg)
else:
	log = log_with_tags(["apiserv"])


def methodroute(*args, **kw):
	def decorator(f):
		if not hasattr(f, 'route'):
			f.route = []
		f.route.append((args, kw))
		return f
	return decorator

def routeapp(obj):
	for attr_name in dir(obj):
		attr = getattr(obj, attr_name)

		if hasattr(attr, 'route'):
			for (args, kws) in attr.route:
				route(*args, **kws)(attr)


# geht sicherlich eleganter und ohne gevent
def debug_exc(exc):
	def just_raise_it(): raise exc
	import gevent
	gevent.spawn(just_raise_it)


def mk_session_id():
	return "".join(choice(ascii_letters) for i in range(64))


class MainNamespace(BaseNamespace):
	def on_test(self, data):
		log("got data:" + data)
		self.emit('testresp', "got: " + str(data))


class Session(object):
	
	def __init__(self, redis_server, session_id, timeout=60*60*24*10000,
			decode=json.loads, encode=json.dumps):
				
		self.session_id = session_id
		self.redis =redis_server
		self.timeout = timeout
		
		self.encode = encode
		self.decode = decode
	
	def __setitem__(self, key, value):
		value = self.encode(value)
		p = self.redis.pipeline()
		new_field = p.hset("session:" + self.session_id, key, value)
		if new_field:
			p.expire("session:" + self.session_id, self.timeout)
		for i in p.execute(): pass
	
	def get(self, key):
		val = self.redis.hget("session:" + self.session_id, key)
		if val is None:
			return None
		return self.decode(val)



class Server:
	
	def __init__(self, redis, api, cookie_args={}, raise_=False):
		
		self.redis = redis
		self.api = api
		self.raise_ = raise_
		self.cookie_args = cookie_args
		
		self._socketio_share = SimpleSocketIOShare()


	def _call_and_encode(self, func, forms, raw):
		
		#set first arg if necessary
		
		log_tags = []
		auth_arg = None
		login_arg = None
		
		session_id = []
		if getattr(func, "auth", False):
			sid = request.cookies.get("sessionId", None)
			
			if not sid:
				raise HTTPError(403)
		
			auth_arg = Session(self.redis, sid).get("uid")
			if auth_arg is None:
				log("false sessionId: {sid} (cookie expired on the server side? redis restart?)".format(sid=sid))
				raise HTTPError(403)
			log_tags.append("user:"+str(auth_arg))
		
			session_id.append(sid)
	
		if getattr(func, "login", False):
			def login_arg(uid):
				sid = mk_session_id()
				session_id.append(sid)
				response.set_cookie("sessionId", sid, self.cookie_args)
				Session(self.redis, sid)["uid"] = uid



		# call function and return value or exception as json
		
		if login_arg is None and auth_arg is None:
			args = []
		elif login_arg is None and auth_arg is not None:
			args = [auth_arg]
		elif login_arg is not None and auth_arg is None:
			args = [login_arg]
		else:
			#this is a mess
			args = [(auth_arg, login_arg)]
	
		
		if hasattr(func, "_class_name"):
			fname = func._class_name + "." + func.__name__
		#elif hasattr(func, "im_class"):
		#	fname = func.im_class + "." + func.__name__
		else:
			fname = func.__name__
		
		log("calling " + fname + "(" + ", ".join(map(repr, args)) + (", " if len(args) and len(forms) else "") + ", ".join(k + "=" + repr(v) for k, v in forms.items()) + ")", ["request"] + log_tags)
		
		try:
			val = func(*args, **forms)
		except Exception if not self.raise_ else None, exc:
				
				if getattr(func, 'html', False):
					traceback.print_exc()
					raise exc
				
				if isinstance(exc, HTTPResponse) or isinstance(exc, HTTPError): #brauchen wir HTTPError?
					raise exc
				
				traceback.print_exc()
				
				if raw:
					raise exc
				else:
					#debug_exc(exc)
					retval = json.dumps(dict(
						status="error",
						data=[exc.__class__.__name__, str(exc)]))
		
		else:
			
			if getattr(func, 'html', False):
				return val
			
			elif raw:
				retval = json.dumps(val)

			else:
				data = dict(
							status="ok",
							data=val)
		
				if session_id and getattr(func, "login", False):
					data["sessionId"] = session_id[0]
			
				retval = json.dumps(data)
		
		resp = json.dumps(json.loads(retval), sort_keys=True, indent=4) # OPTIMIZE: json.loads and json.dumps on every request just for prettier debuging
		log("returning to client: {0}".format(resp), log_tags + ["response"])
		
		return retval



	@methodroute("/api/:version/models/:model<:path>", method=["GET", "POST", "PUT", "DELETE"])
	@methodroute("/api/:version/models/:model/:id<:path>", method=["GET", "PUT", "POST", "DELETE"])
	def _crud(self, version, model, id=None):
		
		method_in_crud = dict(
			POST="create",
			GET="read",
			PUT="update",
			DELETE="delete")[request.method]
		
		if method_in_crud == "read":
			method_in_crud = "read_all" if id is None else "read_one"
	
		try:
			model = getattr(getattr(self.api, version), model)
		except AttributeError:
			raise HTTPError(404)
	
		if not getattr(model, "expose_as_model", False) or not getattr(model, method_in_crud, False):
			raise HTTPError(404)
	
		if method_in_crud == "read_one":
			orig_func = getattr(model, "read_one")
			def func(*args, **kw):
				return orig_func(id, *args, **kw)
			func.__dict__.update(dict((k, v) for (k, v) in orig_func.__dict__.items() if not k.startswith("_")))
		else:
			func = getattr(model, method_in_crud)
	
		raw_body = request.body.read(1024*8)
		if raw_body:
			kwargs = json.loads(raw_body)
		else:
			kwargs = {}
		return self._call_and_encode(func, kwargs, raw=True)



	@methodroute("/api/:version/:function<:path>", method=["GET", "POST"])	
	def _function(self, version, function):
		
		try:
			func = getattr(getattr(self.api, version), function)
		except AttributeError:
			raise HTTPError(404)
	
		if not getattr(func, "exposed", False):
			raise HTTPError(404)
		
		
		form = dict(getattr(request, request.method))
		form = dict((k.decode('utf-8'), v.decode('utf-8')) for k, v in form.iteritems()) 
		return self._call_and_encode(func, form, raw=False)

		

	@methodroute("/socket.io<:re:.*>")
	def _socketio(self):
		session_id = request.get_cookie("session_id")
		log("NO SESSION IN SOCKETIO!!!!!!")
		if not session_id:
			raise ValueError("error on user trying to make socketio stuff. could not get uid from session. user is not loged in?")
		log(session_id)
		session = Session(self.redis, session_id)
		uid = session.get("uid")

		self._socketio_share.update_socket(uid)
		socketio_manage(request.environ, {'': MainNamespace})
	

	def mainloop(self, bind=('127.0.0.1', 8080), policy_server=False, **kw):
		
		routeapp(self)
		
		log('listening on {0} (policy_server={1})'.format(str(bind[0])+":"+str(bind[1]), policy_server))
		SocketIOServer(bind, app().wsgi, namespace="socket.io",
			policy_server=policy_server, **kw).serve_forever()
	
	#def _wsgi_wrapp(wsgi):
	#	def _wsgi(sr, env):
	#		return wsgi(sr, env)
	#	return _wsgi
			
	
	#TODO: this sould not be here
	@methodroute('/<path:path>')
	def static(self, path):
		if path == "":
			path = "index.html"
		return static_file(path, root='../client/public')



if __name__ == "__main__":

	import redis
	import api
	s = Server(redis.StrictRedis(), api)
	s.mainloop()








