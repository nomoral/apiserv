

def expose(fn):
	fn.exposed = True
	return fn

def expose_as_model(cls):
	cls.expose_as_model = True
	
	# just for pretty debuging with staticmethods
	for method in ["create", "read_one", "read_all", "update", "delete"]:
		if hasattr(cls, method):
			setattr(getattr(cls, method), "_class_name", cls.__name__)
	
	return cls

def login(fn):
	fn.login = True
	return fn

def auth(fn):
	fn.auth = True
	return fn

def html(fn):
	fn.html = True
	return fn

