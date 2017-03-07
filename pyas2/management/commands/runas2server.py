from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.utils.translation import ugettext as _
from pyas2 import pyas2init
import pyas2
import os


class Command(BaseCommand):
    help = _(u'Starts the PyAS2 server')

    def handle(self, *args, **options):
        try:
            import cherrypy
            from cherrypy import wsgiserver
        except Exception:
            raise ImportError(_(u'Dependency failure: cherrypy library is needed to start the as2 server'))

        cherrypy.config.update({
            'global': {
                'log.screen': False,
                'log.error_file': os.path.join(pyas2init.gsettings['log_dir'], 'cherrypy_error.log'),
                'server.environment': pyas2init.gsettings['environment']
            }
        })

        # cherrypy handling of static files
        conf = {
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static',
                'tools.staticdir.root': os.path.abspath(
                    os.path.dirname(pyas2.__file__))
            }
        }
        servestaticfiles = cherrypy.tree.mount(None, '/static', conf)

        # cherrypy handling of django
        # was: servedjango = AdminMediaHandler(WSGIHandler())
        # but django does not need the AdminMediaHandler in this setup. is much faster.
        servedjango = WSGIHandler()

        # cherrypy uses a dispatcher in order to handle the serving of
        # static files and django.
        dispatcher = wsgiserver.WSGIPathInfoDispatcher(
            {'/': servedjango, '/static': servestaticfiles})

        pyas2server = wsgiserver.CherryPyWSGIServer(
            bind_addr=('0.0.0.0', pyas2init.gsettings['port']),
            wsgi_app=dispatcher,
            server_name='pyas2-webserver'
        )

        pyas2init.logger.log(
            25, _(u'PyAS2 server running at port: "%s".' % pyas2init.gsettings['port']))

        # handle ssl: cherrypy < 3.2 always uses pyOpenssl. cherrypy >= 3.2
        # uses python buildin ssl (python >= 2.6 has buildin support for ssl).
        ssl_certificate = pyas2init.gsettings['ssl_certificate']
        ssl_private_key = pyas2init.gsettings['ssl_private_key']
        if ssl_certificate and ssl_private_key:
            if cherrypy.__version__ >= '3.2.0':
                adapter_class = wsgiserver.get_ssl_adapter_class('builtin')
                pyas2server.ssl_adapter = adapter_class(ssl_certificate, ssl_private_key)
            else:
                # but: pyOpenssl should be there!
                pyas2server.ssl_certificate = ssl_certificate
                pyas2server.ssl_private_key = ssl_private_key
            pyas2init.logger.log(25, _(u'PyAS2 server uses ssl (https).'))
        else:
            pyas2init.logger.log(25, _(u'PyAS2 server uses plain http (no ssl).'))
        
        # start the cherrypy webserver.
        try:
            pyas2server.start()
        except KeyboardInterrupt:
            pyas2server.stop()
