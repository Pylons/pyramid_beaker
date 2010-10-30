from beaker.session import SessionObject
from beaker.util import coerce_session_params

from pyramid.interfaces import ISession
from zope.interface import implements

def BeakerSessionFactoryConfig(**options):
    """ Return a Pyramid session factory using Beaker session settings
    supplied directly as ``**options``"""
    class PyramidBeakerSessionObject(SessionObject):
        implements(ISession)
        _options = options

        def __init__(self, request):
            SessionObject.__init__(self, request.environ, **self._options)

            def session_callback(request, response):
                exception = getattr(request, 'exception', None)
                if exception is None and self.accessed():
                    self.persist()
                    headers = self.__dict__['_headers']
                    if headers['set_cookie'] and headers['cookie_out']:
                        response.headerlist.append(
                            ('Set-Cookie', headers['cookie_out']))
            request.add_response_callback(session_callback)

        # ISession API

        @property
        def new(self):
            return self.last_accessed is None

        changed = SessionObject.save

        # modifying dictionary methods

        @call_save
        def clear(self):
            return self._session().clear()

        @call_save
        def update(self, d, **kw):
            return self._session().update(d, **kw)

        @call_save
        def setdefault(self, k, d=None):
            return self._session().setdefault(k, d)

        @call_save
        def pop(self, k, d=None):
            return self._session().pop(k, d)

        @call_save
        def popitem(self):
            return self._session().popitem()

        __setitem__ = call_save(SessionObject.__setitem__)
        __delitem__ = call_save(SessionObject.__delitem__)

    return PyramidBeakerSessionObject


def call_save(wrapped):
    """ By default, in non-auto-mode beaker badly wants people to
    call save even though it should know something has changed when
    a mutating method is called.  This hack should be removed if
    Beaker ever starts to do this by default. """
    def save(session, *arg, **kw):
        value = wrapped(session, *arg, **kw)
        session.save()
        return value
    save.__doc__ = wrapped.__doc__
    return save


def session_factory_from_settings(settings):
    """ Return a Pyramid session factory using Beaker session settings
    supplied from a Paste configuration file"""
    prefixes = ('session.', 'beaker.session.')
    options = {}

    # Pull out any config args meant for beaker session. if there are any
    for k, v in settings.items():
        for prefix in prefixes:
            if k.startswith(prefix):
                option_name = k[len(prefix):]
                options[option_name] = v

    options = coerce_session_params(options)
    return BeakerSessionFactoryConfig(**options)
