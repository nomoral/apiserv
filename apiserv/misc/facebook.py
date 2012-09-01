

import urllib2
import urllib
import cgi


from apiserv.decorators import auth, expose
from apiserv import response

#from taglog import log_with_tags

#log = log_with_tags('apiserv.misc.facebook')


class FacebookServerError(Exception):
	pass

class Facebook(object):
	def __init__(self,
			access_token_cb,
			redirect_handler_url,
			facebook_app_id,
			facebook_app_secret,
			permissions=None):
					
		self.access_token_cb = access_token_cb
		self.facebook_app_id = facebook_app_id
		self.facebook_app_secret = facebook_app_secret
		self.redirect_handler_url = redirect_handler_url
		self.permissions = permissions
	
	@auth
	@expose
	def login(self, uid, redirect, **kw):
		redirect = redirect
		response.set_cookie("facebook_redirect", redirect)

		args = dict(
			client_id=self.facebook_app_id,
			redirect_uri=self.redirect_handler_url,
			display="touch")
		
		if self.permissions:
			args["scope"] = ",".join(self.permissions)
		
		args.update(kw)
		
		response.redirect("https://www.facebook.com/dialog/oauth/?" +
			urllib.urlencode(args))

	@auth
	@expose
	def redirect_handler(self, uid, **kw):
		args = dict(
			redirect_uri=self.redirect_handler_url,
			client_id=self.facebook_app_id,
			client_secret=self.facebook_app_secret,
			code=kw['code'])
		
		try:
			resp = urllib2.urlopen("https://graph.facebook.com/oauth/access_token?"
				+ urllib.urlencode(args)).read()
		except urllib2.HTTPError, exc:
			msg = exc.read()
			#log('facebook server returned error: ' + msg)
			raise FacebookServerError(msg)

		access_token = cgi.parse_qs(resp)["access_token"][-1]
		
		self.access_token_cb(uid, access_token)
		
		redirect = response.get_cookie("facebook_redirect")
		response.redirect(redirect)

"""

class FacebookLogout:
	def __init__(self,
			access_token_from_uid,
			redirect,
			facebook_app_id,
			facebook_app_secret):
					
		self.access_token_from_uid = access_token_from_uid
		self.redirect = redirect
		self.facebook_app_id = facebook_app_id
		self.facebook_app_secret = facebook_app_secret


"""
