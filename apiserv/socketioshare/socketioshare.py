

import urllib2

import stupidshare




class PeerSocketIOShare(object):
	
	def __init__(self, this_server, sockets={}): 
		self.this_server = this_server
		self.sockets = sockets
	
	def update_socket(self, uid, socket):
		self.redis.set('socketio:' + uid, self.this_server)
		self.sockets[uid] = socket
	
	def push(self, uid, msg):
		socketio_loc = self.redis.get('socketio:' + uid)
		if socket_loc is None:
			raise ValueError("socket location not found")
		
		urllib2.urlopen(socketio_loc, dict(uid=uid, msg=msg))
	
	def handle_push(self, env, start_response):
		adsfdasfdasfda

class SimpleSocketIOShare(object):
	
	def __init__(self, sockets=None):
		if sockets is None:
			try:
				sockets = stupidshare.socket
			except AttributeError:
				sockets = stupidshare.socket = {}
		self._sockets = sockets
	
	def update_socket(self, sid, socket):
		print "update:", sid, socket
		self._socket[sid] = socket
	
	def send_packet(self, sid, packet):
		self._sockets[sid].send_packet(packet)



