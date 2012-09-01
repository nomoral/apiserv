from bottle import redirect
import bottle as _bottle

set_cookie = _bottle.response.set_cookie
get_cookie = _bottle.request.get_cookie

