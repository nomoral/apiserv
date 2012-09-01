

apiserv
=======


An example says more than thousands words (example/api/test.py):



	from apiserv.decorators import auth, expose, login, expose_as_model, html
	from apiserv.misc import Facebook


	@expose
	def hello():
		return "hello world"

	@expose
	def echo(data):
		return data


	@expose
	def double(num):
		return int(num) * 2



	@expose_as_model
	class User:
	
	
		# access example http://localhost:8080/api/test/models/User
		@staticmethod
		def read_all():
			return [dict(id=0, name="Foo Bar")]
	
		# access example http://localhost:8080/api/test/models/User/0
		@staticmethod
		def read_one(id):
			assert int(id) == 0
			return User.read_all()[0]
	
		# PUT
		@staticmethod
		def update(data):
			raise NotImplemented()



	@login
	@expose
	def login(login, nick, pwd):
		if nick == "user" and pwd ==  "pwd":
			login(nick)
			return True
		return False


	@auth
	@expose
	def needs_login(nick):
		return "you are logged in as: " + nick




	def handle_access_token(uid, access_token):
		print "got fb access token from {}, its: {}".format(uid, access_token)

	facebook = Facebook(
		access_token_cb=handle_access_token,
		redirect_handler_url="http://mydomain.com/api/test/facebookRedirectHandler/",
		facebook_app_id="1234 fb app id",
		facebook_app_secret="my app secret",
		permissions=['publish_actions'])

	facebook_login_page = facebook.login
	facebook_redirect_handler = facebook.redirect_handler









