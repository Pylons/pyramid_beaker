from beaker.session import SessionObject
from beaker.util import coerce_session_params

## session.type = file
## session.data_dir = %(here)s/data/sessions/data
## session.lock_dir = %(here)s/data/sessions/lock
## session.key = {{project}}
## session.secret = your_app_secret_string

def BeakerSessionFactoryConfig(**options):
    """ Return a Pyramid session factory using Beaker session settings
    supplied directly as ``**options``"""
    if not 'auto' in options:
        options['auto'] = True 

    class PyramidBeakerSessionObject(SessionObject):
        _options = options
        def __init__(self, request):
            SessionObject.__init__(self, request.environ, **self._options)
            def session_callback(request, response):
                exception = getattr(request, 'exception', None)
                if  exception is None:
                    if self.accessed():
                        self.persist()
                        if self.__dict__['_headers']['set_cookie']:
                            cook = self.__dict__['_headers']['cookie_out']
                            if cook:
                                response.headerlist.append(('Set-Cookie', cook))
            request.add_response_callback(session_callback)

        @property
        def new(self):
            return self.last_accessed is None

        changed = SessionObject.save

        # modifying dictionary methods
        # XXX these methods are missing
        # clear = call_save(SessionObject.clear)
        # update = call_save(SessionObject.update)
        # setdefault = call_save(SessionObject.setdefault)
        # pop = call_save(SessionObject.pop)
        # popitem = call_save(SessionObject.popitem)
        __setitem__ = call_save(SessionObject.__setitem__)
        __delitem__ = call_save(SessionObject.__delitem__)

    return PyramidBeakerSessionObject

def call_save(wrapped):
    # XXX by default, in non-auto-mode beaker badly wants people to
    # call save even though it should know something has changed when
    # a mutating method is called.  This hack should be removed if
    # Beaker ever starts to do this by default.
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
    
    
