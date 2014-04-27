from twisted.internet import reactor, defer
from twisted.web import server, resource
from hello_app import app

'''
This is, Chrome browser somewhat aside, working nicely asynchronously.
'''

# run in under twisted through wsgi
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
site = Site(resource)

if __name__ == '__main__':
	reactor.listenTCP( 5001, site )
	reactor.run()