from twisted.internet import reactor, defer
from twisted.web import server, resource
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site

# import app
from hello_app import app

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
site = Site(resource)

if __name__ == '__main__':
	print "Firing up..."
	reactor.listenTCP( 5001, site )
	reactor.run()	